"""AdventureScore: a weighted heuristic that ranks seeded destinations for a traveler.

See documentation/recommendation_algorithm.md for the full write-up of each factor
and the reasoning behind the default weights.
"""

from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.destination import Destination
from app.services.weather import DayForecast, get_forecasts_batch

# Near-term outlook used for destination-level scoring (not tied to a specific
# trip length, unlike itinerary generation -- just "is the weather good right now").
WEATHER_OUTLOOK_DAYS = 3

DEFAULT_WEIGHTS: dict[str, float] = {
    "budget_fit": 0.25,
    "interest_match": 0.25,
    "uniqueness": 0.15,
    "cost_efficiency": 0.15,
    "travel_difficulty": 0.10,
    "weather": 0.10,
}


def _score_budget_fit(destination: Destination, max_budget: float | None) -> float:
    if max_budget is None:
        return 0.5
    if max_budget <= 0:
        return 0.0
    if destination.budget_per_day <= max_budget:
        return 1.0
    overage_ratio = (destination.budget_per_day - max_budget) / max_budget
    return max(0.0, 1.0 - overage_ratio)


def _score_interest_match(destination: Destination, requested_interests: set[str]) -> float:
    if not requested_interests:
        return 0.5
    destination_tags = {tag.lower() for tag in destination.interest_list()}
    matches = requested_interests & destination_tags
    return min(1.0, len(matches) / len(requested_interests))


def _score_uniqueness(destination: Destination) -> float:
    return max(0.0, min(1.0, destination.uniqueness_score / 10))


def _score_cost_efficiency(destination: Destination, min_cost: float, max_cost: float) -> float:
    if max_cost <= min_cost:
        return 1.0
    return max(0.0, min(1.0, (max_cost - destination.budget_per_day) / (max_cost - min_cost)))


def _score_travel_difficulty(destination: Destination) -> float:
    return max(0.0, min(1.0, 1.0 - destination.travel_difficulty / 10))


def _score_weather(forecast: list[DayForecast] | None) -> float:
    if not forecast:
        return 0.5

    avg_precip_probability = mean(day.precipitation_probability for day in forecast) / 100
    avg_temperature = mean((day.temperature_max + day.temperature_min) / 2 for day in forecast)

    precip_score = 1.0 - avg_precip_probability
    # Comfort peaks around 20C and falls off the further away it gets.
    temp_score = max(0.0, 1.0 - abs(avg_temperature - 20) / 25)

    return max(0.0, min(1.0, 0.6 * precip_score + 0.4 * temp_score))


def _weather_summary(forecast: list[DayForecast] | None) -> str | None:
    if not forecast:
        return None
    avg_precip_probability = round(mean(day.precipitation_probability for day in forecast))
    return f"{forecast[0].condition}, ~{avg_precip_probability}% avg rain chance over the next {len(forecast)} days"


def get_top_recommendations(
    db: Session,
    max_budget: float | None = None,
    interests: str | None = None,
    top_n: int = 10,
    weights: dict[str, float] | None = None,
) -> list[tuple[Destination, float, dict[str, float], str | None]]:
    """Rank every seeded destination by AdventureScore and return the top `top_n`.

    Returns a list of (destination, adventure_score, score_breakdown,
    weather_summary) tuples, sorted by adventure_score descending (ties broken
    alphabetically by name).
    """
    active_weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    destinations = list(db.execute(select(Destination)).scalars().all())
    if not destinations:
        return []

    requested_interests = (
        {tag.strip().lower() for tag in interests.split(",") if tag.strip()} if interests else set()
    )

    costs = [d.budget_per_day for d in destinations]
    min_cost, max_cost = min(costs), max(costs)

    forecasts = get_forecasts_batch(
        [(d.id, d.latitude, d.longitude) for d in destinations], WEATHER_OUTLOOK_DAYS
    )

    scored: list[tuple[Destination, float, dict[str, float], str | None]] = []
    for destination in destinations:
        forecast = forecasts.get(destination.id)
        breakdown = {
            "budget_fit": round(_score_budget_fit(destination, max_budget), 4),
            "interest_match": round(_score_interest_match(destination, requested_interests), 4),
            "uniqueness": round(_score_uniqueness(destination), 4),
            "cost_efficiency": round(_score_cost_efficiency(destination, min_cost, max_cost), 4),
            "travel_difficulty": round(_score_travel_difficulty(destination), 4),
            "weather": round(_score_weather(forecast), 4),
        }
        adventure_score = round(
            100 * sum(breakdown[factor] * weight for factor, weight in active_weights.items()), 1
        )
        scored.append((destination, adventure_score, breakdown, _weather_summary(forecast)))

    scored.sort(key=lambda item: (-item[1], item[0].name))
    return scored[:top_n]
