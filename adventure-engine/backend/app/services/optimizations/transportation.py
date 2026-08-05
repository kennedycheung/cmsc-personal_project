"""Origin -> destination transportation cost estimation, by great-circle
distance and travel mode, party-size-aware.

No free real fare API exists (same gap as the deal ingestion pipeline), so
this is a documented-assumption cost curve in the style of the other
backpacker-optimization calculators:

Mode = overland if distance <= FLIGHT_THRESHOLD_KM else flight
OverlandCost = distance_km * OVERLAND_COST_PER_KM_USD * ceil(travelers / VEHICLE_CAPACITY)
FlightCost = (FLIGHT_BASE_FARE_USD + distance_km * FLIGHT_COST_PER_KM_USD) * travelers

Overland cost is shared across a shared vehicle (up to its seating
capacity, beyond which another vehicle -- and its cost -- is needed);
flight fares are priced and paid per person, not shareable.

See documentation/backpacker_optimizations.md for the full write-up.
"""

import math
from dataclasses import dataclass
from enum import Enum

from app.services.optimizations.constants import OVERLAND_COST_PER_KM_USD
from app.services.optimizations.geo import haversine_km

# Below this distance, overland transport (bus/train/rideshare) is assumed
# more practical than flying -- short-haul flights rarely make sense once
# airport transfer time/cost is factored in. Above it, flying is assumed.
FLIGHT_THRESHOLD_KM = 500.0

# Rough global-average economy short/medium-haul fare curve: a flat booking/
# fees base plus a per-km rate. Not tied to any real airline's pricing.
FLIGHT_BASE_FARE_USD = 80.0
FLIGHT_COST_PER_KM_USD = 0.09

# Typical rental car / rideshare seating capacity, used to decide how many
# vehicles (and therefore how many times the overland cost) a party needs.
VEHICLE_CAPACITY = 4


class TransportMode(str, Enum):
    OVERLAND = "overland"
    FLIGHT = "flight"


@dataclass
class TransportationCostResult:
    distance_km: float
    mode: TransportMode
    travelers: int
    total_cost: float
    cost_per_person: float


def estimate_transportation_cost(
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    travelers: int = 1,
) -> TransportationCostResult:
    distance_km = haversine_km(origin_lat, origin_lon, destination_lat, destination_lon)
    travelers = max(1, travelers)

    if distance_km <= FLIGHT_THRESHOLD_KM:
        mode = TransportMode.OVERLAND
        vehicles_needed = math.ceil(travelers / VEHICLE_CAPACITY)
        total_cost = distance_km * OVERLAND_COST_PER_KM_USD * vehicles_needed
    else:
        mode = TransportMode.FLIGHT
        total_cost = (FLIGHT_BASE_FARE_USD + distance_km * FLIGHT_COST_PER_KM_USD) * travelers

    return TransportationCostResult(
        distance_km=round(distance_km, 1),
        mode=mode,
        travelers=travelers,
        total_cost=round(total_cost, 2),
        cost_per_person=round(total_cost / travelers, 2),
    )
