"""Overnight transportation savings.

LodgingPerNight = destination.budget_per_day * LODGING_SHARE_OF_BUDGET
TransportPremium = OvernightPrice - DaytimePrice
NetSavings = (NightsSaved * LodgingPerNight) - TransportPremium

See documentation/backpacker_optimizations.md for the full derivation and a worked example.
"""

from dataclasses import dataclass

from app.models.destination import Destination
from app.services.optimizations.constants import LODGING_SHARE_OF_BUDGET


@dataclass
class OvernightTransportResult:
    lodging_per_night: float
    transport_premium: float
    nights_saved: int
    net_savings: float
    worth_it: bool


def evaluate_overnight_transport(
    destination: Destination,
    overnight_price: float,
    daytime_price: float,
    nights_saved: int = 1,
) -> OvernightTransportResult:
    lodging_per_night = destination.budget_per_day * LODGING_SHARE_OF_BUDGET
    transport_premium = overnight_price - daytime_price
    net_savings = (nights_saved * lodging_per_night) - transport_premium

    return OvernightTransportResult(
        lodging_per_night=round(lodging_per_night, 2),
        transport_premium=round(transport_premium, 2),
        nights_saved=nights_saved,
        net_savings=round(net_savings, 2),
        worth_it=net_savings > 0,
    )
