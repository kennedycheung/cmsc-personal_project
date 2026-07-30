"""Open-jaw routing.

BacktrackDistanceKm = haversine(LastStop, EntryCity)
BacktrackCost = BacktrackDistanceKm * OVERLAND_COST_PER_KM_USD
BacktrackTimeHours = BacktrackDistanceKm / OVERLAND_SPEED_KMH
FarePremium = (OneWayFareOut + OneWayFareBack) - RoundTripFare
NetSavings = BacktrackCost - FarePremium

See documentation/backpacker_optimizations.md for the full derivation and a worked example.
"""

from dataclasses import dataclass

from app.models.destination import Destination
from app.services.optimizations.constants import (
    OVERLAND_COST_PER_KM_USD,
    OVERLAND_MAX_REASONABLE_KM,
    OVERLAND_SPEED_KMH,
)
from app.services.optimizations.geo import haversine_km


@dataclass
class OpenJawResult:
    backtrack_distance_km: float
    backtrack_cost: float
    backtrack_time_hours: float
    fare_premium: float
    net_savings: float
    worth_it: bool
    unrealistic_overland_distance: bool


def evaluate_open_jaw(
    entry: Destination,
    exit_: Destination,
    round_trip_fare: float = 0.0,
    one_way_fare_out: float = 0.0,
    one_way_fare_back: float = 0.0,
) -> OpenJawResult:
    # The backtrack a round trip would require: from wherever the overland
    # leg ends (exit) back to the entry city, to catch a flight home from there.
    distance_km = haversine_km(exit_.latitude, exit_.longitude, entry.latitude, entry.longitude)
    backtrack_cost = distance_km * OVERLAND_COST_PER_KM_USD
    backtrack_time_hours = distance_km / OVERLAND_SPEED_KMH

    fare_premium = (one_way_fare_out + one_way_fare_back) - round_trip_fare
    net_savings = backtrack_cost - fare_premium

    return OpenJawResult(
        backtrack_distance_km=round(distance_km, 1),
        backtrack_cost=round(backtrack_cost, 2),
        backtrack_time_hours=round(backtrack_time_hours, 1),
        fare_premium=round(fare_premium, 2),
        net_savings=round(net_savings, 2),
        # Monetary criterion only -- the backtrack time is *always* saved by
        # not returning to the entry city, independent of the fare premium's sign.
        worth_it=net_savings > 0,
        unrealistic_overland_distance=distance_km > OVERLAND_MAX_REASONABLE_KM,
    )
