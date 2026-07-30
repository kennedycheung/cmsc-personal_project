"""Nearby airport optimization.

EffectiveCost(i) = BaselineFare(i) + GroundTransportCost(i)
                    + (GroundTransportMinutes(i) / 60) * TIME_VALUE_PER_HOUR_USD
Recommended = argmin_i EffectiveCost(i)
SavingsVsPrimary = EffectiveCost(primary) - EffectiveCost(Recommended)

See documentation/backpacker_optimizations.md for the full derivation and a worked example.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.airport import Airport
from app.services.optimizations.constants import TIME_VALUE_PER_HOUR_USD


class NoAirportDataError(Exception):
    """Raised when a destination has no modeled airport alternatives."""


@dataclass
class AirportOption:
    airport: Airport
    effective_cost: float


@dataclass
class AirportOptimizationResult:
    options: list[AirportOption]
    recommended: Airport
    primary: Airport
    savings_vs_primary: float


def _effective_cost(airport: Airport, time_value_per_hour: float) -> float:
    return (
        airport.baseline_fare_usd
        + airport.ground_transport_cost_usd
        + (airport.ground_transport_minutes / 60.0) * time_value_per_hour
    )


def optimize_airport_choice(
    db: Session, destination_id: int, time_value_per_hour: float = TIME_VALUE_PER_HOUR_USD
) -> AirportOptimizationResult:
    """Raises NoAirportDataError if the destination has no modeled airports."""
    airports = list(
        db.execute(select(Airport).where(Airport.destination_id == destination_id)).scalars().all()
    )
    if not airports:
        raise NoAirportDataError(destination_id)

    options = sorted(
        (AirportOption(airport=a, effective_cost=round(_effective_cost(a, time_value_per_hour), 2)) for a in airports),
        key=lambda option: option.effective_cost,
    )

    primary = next((a for a in airports if a.is_primary), airports[0])
    primary_cost = _effective_cost(primary, time_value_per_hour)
    recommended_cost = options[0].effective_cost

    return AirportOptimizationResult(
        options=options,
        recommended=options[0].airport,
        primary=primary,
        savings_vs_primary=round(primary_cost - recommended_cost, 2),
    )
