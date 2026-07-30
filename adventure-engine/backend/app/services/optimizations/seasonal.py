"""Seasonal arbitrage.

SeasonalCost(month) = destination.budget_per_day * Multiplier(month)
BestMonth = argmin_month SeasonalCost(month)
PeakMonth = argmax_month SeasonalCost(month)
SavingsVsPeak = SeasonalCost(PeakMonth) - SeasonalCost(BestMonth)
SavingsVsCurrent = SeasonalCost(CurrentMonth) - SeasonalCost(BestMonth)

See documentation/backpacker_optimizations.md for the full derivation and a worked example.
"""

from dataclasses import dataclass

from app.models.destination import Destination

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


@dataclass
class MonthCost:
    month: int
    month_name: str
    multiplier: float
    cost: float


@dataclass
class SeasonalArbitrageResult:
    months: list[MonthCost]
    best_month: MonthCost
    peak_month: MonthCost
    current_month: MonthCost
    savings_vs_peak: float
    savings_vs_current: float


def evaluate_seasonal_arbitrage(destination: Destination, current_month: int) -> SeasonalArbitrageResult:
    """current_month is 1-12."""
    multipliers = destination.seasonal_multiplier_list()
    months = [
        MonthCost(
            month=index + 1,
            month_name=MONTH_NAMES[index],
            multiplier=multiplier,
            cost=round(destination.budget_per_day * multiplier, 2),
        )
        for index, multiplier in enumerate(multipliers)
    ]

    best_month = min(months, key=lambda m: m.cost)
    peak_month = max(months, key=lambda m: m.cost)
    current = months[current_month - 1]

    return SeasonalArbitrageResult(
        months=months,
        best_month=best_month,
        peak_month=peak_month,
        current_month=current,
        savings_vs_peak=round(peak_month.cost - best_month.cost, 2),
        savings_vs_current=round(current.cost - best_month.cost, 2),
    )
