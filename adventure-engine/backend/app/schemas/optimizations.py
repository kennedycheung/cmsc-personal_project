"""Response shapes for the six backpacker optimization calculators.
See documentation/backpacker_optimizations.md for the math behind each.
"""

from pydantic import BaseModel

from app.schemas.airport import AirportRead
from app.schemas.destination import DestinationRead


class AirportOptionRead(BaseModel):
    airport: AirportRead
    effective_cost: float


class AirportOptimizationRead(BaseModel):
    destination: DestinationRead
    options: list[AirportOptionRead]
    recommended: AirportRead
    primary: AirportRead
    savings_vs_primary: float
    time_value_per_hour_usd: float


class OvernightTransportRead(BaseModel):
    destination: DestinationRead
    lodging_per_night: float
    overnight_price: float
    daytime_price: float
    transport_premium: float
    nights_saved: int
    net_savings: float
    worth_it: bool


class OpenJawRead(BaseModel):
    entry: DestinationRead
    exit: DestinationRead
    backtrack_distance_km: float
    backtrack_cost: float
    backtrack_time_hours: float
    fare_premium: float
    net_savings: float
    worth_it: bool
    unrealistic_overland_distance: bool


class PositioningRead(BaseModel):
    hub: DestinationRead
    direct_itinerary_cost: float
    positioning_cost: float
    layover_lodging_cost: float
    net_savings: float
    worth_it: bool


class MonthCostRead(BaseModel):
    month: int
    month_name: str
    multiplier: float
    cost: float


class SeasonalArbitrageRead(BaseModel):
    destination: DestinationRead
    months: list[MonthCostRead]
    best_month: MonthCostRead
    peak_month: MonthCostRead
    current_month: MonthCostRead
    savings_vs_peak: float
    savings_vs_current: float


class TransportationCostRead(BaseModel):
    distance_km: float
    mode: str
    travelers: int
    total_cost: float
    cost_per_person: float


class BudgetAllocationRead(BaseModel):
    total_budget: float
    transportation_cost: float
    remaining_budget: float
    lodging: float
    food: float
    activities: float
    local_transport: float
    contingency: float
    effective_daily_budget_per_person: float
    insufficient: bool


class CurrencyArbitrageRead(BaseModel):
    destination: DestinationRead
    home_currency: str
    local_currency: str
    available: bool
    current_rate: float | None = None
    baseline_rate: float | None = None
    adjusted_budget_per_day: float | None = None
    savings: float | None = None
    arbitrage_percent: float | None = None
