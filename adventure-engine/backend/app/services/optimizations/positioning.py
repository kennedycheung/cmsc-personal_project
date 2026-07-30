"""Positioning trips.

PositioningCost = Fare(Home -> Hub) + Fare(Hub -> Final)
                   + ExtraNights * (Hub.budget_per_day * LODGING_SHARE_OF_BUDGET)
NetSavings = DirectItineraryCost - PositioningCost

See documentation/backpacker_optimizations.md for the full derivation and a worked example.
"""

from dataclasses import dataclass

from app.models.destination import Destination
from app.services.optimizations.constants import LODGING_SHARE_OF_BUDGET


@dataclass
class PositioningResult:
    positioning_cost: float
    layover_lodging_cost: float
    net_savings: float
    worth_it: bool


def evaluate_positioning_trip(
    hub: Destination,
    direct_itinerary_cost: float,
    fare_home_to_hub: float,
    fare_hub_to_final: float,
    extra_nights: int = 0,
) -> PositioningResult:
    layover_lodging_cost = extra_nights * hub.budget_per_day * LODGING_SHARE_OF_BUDGET
    positioning_cost = fare_home_to_hub + fare_hub_to_final + layover_lodging_cost
    net_savings = direct_itinerary_cost - positioning_cost

    return PositioningResult(
        positioning_cost=round(positioning_cost, 2),
        layover_lodging_cost=round(layover_lodging_cost, 2),
        net_savings=round(net_savings, 2),
        worth_it=net_savings > 0,
    )
