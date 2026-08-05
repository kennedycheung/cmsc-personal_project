"""Splits a total trip budget across lodging/food/activities/local-transport/
contingency once transportation cost is known, party-size-aware.

RemainingBudget = TotalBudget - TransportationCost
Each category = RemainingBudget * its documented share (shares sum to 1.0,
extending the LODGING_SHARE_OF_BUDGET pattern already used elsewhere).
EffectiveDailyBudgetPerPerson = RemainingBudget / (Days * Travelers) -- the
number meant to feed AdventureScore's budget-fit scoring
(recommendation.py's max_budget), once wired in.

See documentation/backpacker_optimizations.md for the full write-up.
"""

from dataclasses import dataclass

LODGING_SHARE = 0.35
FOOD_SHARE = 0.25
ACTIVITIES_SHARE = 0.20
LOCAL_TRANSPORT_SHARE = 0.10
CONTINGENCY_SHARE = 0.10


@dataclass
class BudgetAllocationResult:
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


def allocate_budget(
    total_budget: float,
    transportation_cost: float,
    days: int,
    travelers: int = 1,
) -> BudgetAllocationResult:
    days = max(1, days)
    travelers = max(1, travelers)

    remaining = total_budget - transportation_cost
    insufficient = remaining <= 0
    remaining = max(0.0, remaining)

    return BudgetAllocationResult(
        total_budget=round(total_budget, 2),
        transportation_cost=round(transportation_cost, 2),
        remaining_budget=round(remaining, 2),
        lodging=round(remaining * LODGING_SHARE, 2),
        food=round(remaining * FOOD_SHARE, 2),
        activities=round(remaining * ACTIVITIES_SHARE, 2),
        local_transport=round(remaining * LOCAL_TRANSPORT_SHARE, 2),
        contingency=round(remaining * CONTINGENCY_SHARE, 2),
        effective_daily_budget_per_person=round(remaining / (days * travelers), 2),
        insufficient=insufficient,
    )
