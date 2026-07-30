from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.destination import Destination
from app.schemas.airport import AirportRead
from app.schemas.destination import DestinationRead
from app.schemas.optimizations import (
    AirportOptimizationRead,
    AirportOptionRead,
    CurrencyArbitrageRead,
    MonthCostRead,
    OpenJawRead,
    OvernightTransportRead,
    PositioningRead,
    SeasonalArbitrageRead,
)
from app.services.optimizations.airports import NoAirportDataError, optimize_airport_choice
from app.services.optimizations.constants import TIME_VALUE_PER_HOUR_USD
from app.services.optimizations.currency import (
    CurrencyRateUnavailableError,
    evaluate_currency_arbitrage,
    evaluate_currency_arbitrage_batch,
)
from app.services.optimizations.open_jaw import evaluate_open_jaw
from app.services.optimizations.overnight_transport import evaluate_overnight_transport
from app.services.optimizations.positioning import evaluate_positioning_trip
from app.services.optimizations.seasonal import evaluate_seasonal_arbitrage

router = APIRouter(prefix="/optimizations", tags=["optimizations"])


def _get_destination_or_404(db: Session, destination_id: int) -> Destination:
    destination = db.get(Destination, destination_id)
    if destination is None:
        raise HTTPException(status_code=404, detail=f"Destination {destination_id} not found")
    return destination


@router.get("/airports/{destination_id}", response_model=AirportOptimizationRead)
def get_airport_optimization(
    destination_id: int,
    time_value_per_hour: float = Query(TIME_VALUE_PER_HOUR_USD, ge=0),
    db: Session = Depends(get_db),
) -> AirportOptimizationRead:
    destination = _get_destination_or_404(db, destination_id)
    try:
        result = optimize_airport_choice(db, destination_id, time_value_per_hour)
    except NoAirportDataError:
        raise HTTPException(
            status_code=404, detail=f"No alternate-airport data modeled for destination {destination_id}"
        )

    return AirportOptimizationRead(
        destination=DestinationRead.from_model(destination),
        options=[
            AirportOptionRead(airport=AirportRead.model_validate(o.airport), effective_cost=o.effective_cost)
            for o in result.options
        ],
        recommended=AirportRead.model_validate(result.recommended),
        primary=AirportRead.model_validate(result.primary),
        savings_vs_primary=result.savings_vs_primary,
        time_value_per_hour_usd=time_value_per_hour,
    )


@router.get("/overnight-transport/{destination_id}", response_model=OvernightTransportRead)
def get_overnight_transport_savings(
    destination_id: int,
    overnight_price: float = Query(..., ge=0),
    daytime_price: float = Query(..., ge=0),
    nights_saved: int = Query(1, ge=1, le=10),
    db: Session = Depends(get_db),
) -> OvernightTransportRead:
    destination = _get_destination_or_404(db, destination_id)
    result = evaluate_overnight_transport(destination, overnight_price, daytime_price, nights_saved)

    return OvernightTransportRead(
        destination=DestinationRead.from_model(destination),
        lodging_per_night=result.lodging_per_night,
        overnight_price=overnight_price,
        daytime_price=daytime_price,
        transport_premium=result.transport_premium,
        nights_saved=result.nights_saved,
        net_savings=result.net_savings,
        worth_it=result.worth_it,
    )


@router.get("/open-jaw", response_model=OpenJawRead)
def get_open_jaw_evaluation(
    entry_destination_id: int = Query(...),
    exit_destination_id: int = Query(...),
    round_trip_fare: float = Query(0, ge=0),
    one_way_fare_out: float = Query(0, ge=0),
    one_way_fare_back: float = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> OpenJawRead:
    entry = _get_destination_or_404(db, entry_destination_id)
    exit_ = _get_destination_or_404(db, exit_destination_id)
    result = evaluate_open_jaw(entry, exit_, round_trip_fare, one_way_fare_out, one_way_fare_back)

    return OpenJawRead(
        entry=DestinationRead.from_model(entry),
        exit=DestinationRead.from_model(exit_),
        backtrack_distance_km=result.backtrack_distance_km,
        backtrack_cost=result.backtrack_cost,
        backtrack_time_hours=result.backtrack_time_hours,
        fare_premium=result.fare_premium,
        net_savings=result.net_savings,
        worth_it=result.worth_it,
        unrealistic_overland_distance=result.unrealistic_overland_distance,
    )


@router.get("/positioning", response_model=PositioningRead)
def get_positioning_evaluation(
    hub_destination_id: int = Query(...),
    direct_itinerary_cost: float = Query(..., ge=0),
    fare_home_to_hub: float = Query(..., ge=0),
    fare_hub_to_final: float = Query(..., ge=0),
    extra_nights: int = Query(0, ge=0, le=30),
    db: Session = Depends(get_db),
) -> PositioningRead:
    hub = _get_destination_or_404(db, hub_destination_id)
    result = evaluate_positioning_trip(hub, direct_itinerary_cost, fare_home_to_hub, fare_hub_to_final, extra_nights)

    return PositioningRead(
        hub=DestinationRead.from_model(hub),
        direct_itinerary_cost=direct_itinerary_cost,
        positioning_cost=result.positioning_cost,
        layover_lodging_cost=result.layover_lodging_cost,
        net_savings=result.net_savings,
        worth_it=result.worth_it,
    )


@router.get("/seasonal/{destination_id}", response_model=SeasonalArbitrageRead)
def get_seasonal_arbitrage(
    destination_id: int,
    month: int = Query(default=None, ge=1, le=12, description="1-12; defaults to the current month"),
    db: Session = Depends(get_db),
) -> SeasonalArbitrageRead:
    destination = _get_destination_or_404(db, destination_id)
    current_month = month if month is not None else date.today().month
    result = evaluate_seasonal_arbitrage(destination, current_month)

    def _to_read(m) -> MonthCostRead:
        return MonthCostRead(month=m.month, month_name=m.month_name, multiplier=m.multiplier, cost=m.cost)

    return SeasonalArbitrageRead(
        destination=DestinationRead.from_model(destination),
        months=[_to_read(m) for m in result.months],
        best_month=_to_read(result.best_month),
        peak_month=_to_read(result.peak_month),
        current_month=_to_read(result.current_month),
        savings_vs_peak=result.savings_vs_peak,
        savings_vs_current=result.savings_vs_current,
    )


def _to_currency_read(destination: Destination, home_currency: str, result) -> CurrencyArbitrageRead:
    if result is None:
        return CurrencyArbitrageRead(
            destination=DestinationRead.from_model(destination),
            home_currency=home_currency,
            local_currency=destination.currency,
            available=False,
        )
    return CurrencyArbitrageRead(
        destination=DestinationRead.from_model(destination),
        home_currency=home_currency,
        local_currency=result.local_currency,
        available=True,
        current_rate=result.current_rate,
        baseline_rate=result.baseline_rate,
        adjusted_budget_per_day=result.adjusted_budget_per_day,
        savings=result.savings,
        arbitrage_percent=result.arbitrage_percent,
    )


@router.get("/currency/{destination_id}", response_model=CurrencyArbitrageRead)
def get_currency_arbitrage(
    destination_id: int,
    home_currency: str = Query("USD", min_length=3, max_length=3),
    db: Session = Depends(get_db),
) -> CurrencyArbitrageRead:
    destination = _get_destination_or_404(db, destination_id)
    home_currency = home_currency.upper()

    try:
        result = evaluate_currency_arbitrage(destination.budget_per_day, destination.currency, home_currency)
    except CurrencyRateUnavailableError:
        result = None

    return _to_currency_read(destination, home_currency, result)


@router.get("/currency", response_model=list[CurrencyArbitrageRead])
def list_currency_arbitrage(
    home_currency: str = Query("USD", min_length=3, max_length=3),
    db: Session = Depends(get_db),
) -> list[CurrencyArbitrageRead]:
    home_currency = home_currency.upper()
    destinations = list(db.execute(select(Destination)).scalars().all())

    results = evaluate_currency_arbitrage_batch(
        [(d.id, d.budget_per_day, d.currency) for d in destinations], home_currency
    )

    return [_to_currency_read(d, home_currency, results.get(d.id)) for d in destinations]
