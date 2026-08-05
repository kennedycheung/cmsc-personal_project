"""Step 6: scores each enriched attraction against the traveler's request.

Weighted sum over interest match, distance, rating, popularity, price fit,
hours fit, a current-events bonus, and weather suitability -- documented
weights table, same convention as itinerary.py's SCORE_WEIGHTS.
"""

import math

from app.services.discovery.types import DiscoveryRequest, EnrichedAttraction, RankedAttraction
from app.services.optimizations.geo import haversine_km
from app.services.weather import DayForecast, is_bad_weather, is_good_weather

SCORE_WEIGHTS: dict[str, float] = {
    "interest_match": 0.25,
    "distance": 0.15,
    "rating": 0.15,
    "popularity": 0.10,
    "price_fit": 0.10,
    "hours_fit": 0.10,
    "current_events": 0.05,
    "weather_fit": 0.10,
}

MAX_RELEVANT_DISTANCE_KM = 20.0  # beyond this, the distance factor bottoms out at 0
POPULARITY_REFERENCE_REVIEWS = 1000  # review count treated as "maximally popular"

# Categories/tags with an outdoor lean, used by the weather-suitability
# factor (here) and the "Best Rainy Day" bucket (buckets.py) -- a
# documented, non-exhaustive assumption list, same spirit as itinerary.py's
# _MORNING_TAGS/_EVENING_TAGS/_LATE_NIGHT_TAGS.
OUTDOOR_CATEGORY_HINTS = {"park", "hike", "hiking", "nature", "beach", "garden", "outdoor", "viewpoint"}


def _score_interest_match(attraction: EnrichedAttraction, interests: list[str]) -> float:
    if not interests:
        return 0.5
    tags = {c.lower() for c in attraction.categories}
    matches = set(interests) & tags
    return min(1.0, len(matches) / len(interests))


def _score_distance(attraction: EnrichedAttraction, request: DiscoveryRequest) -> float:
    distance_km = haversine_km(
        request.latitude, request.longitude, attraction.candidate.latitude, attraction.candidate.longitude
    )
    return max(0.0, 1.0 - distance_km / MAX_RELEVANT_DISTANCE_KM)


def _score_rating(attraction: EnrichedAttraction) -> float:
    if attraction.rating is None:
        return 0.5
    return max(0.0, min(1.0, attraction.rating / 5))


def _score_popularity(attraction: EnrichedAttraction) -> float:
    review_count = attraction.review_count or 0
    return min(1.0, math.log1p(review_count) / math.log1p(POPULARITY_REFERENCE_REVIEWS))


def _score_price_fit(attraction: EnrichedAttraction, max_budget: float | None) -> float:
    if attraction.price_level is None:
        return 0.5
    if max_budget is not None and max_budget <= 0:
        return 1.0 if attraction.price_level == 0 else 0.0
    return max(0.0, 1.0 - attraction.price_level / 4)


def _score_hours_fit(attraction: EnrichedAttraction) -> float:
    # Best-effort: this app doesn't know the traveler's exact visit time for
    # a discovery request (unlike itinerary.py's per-slot scheduling), so
    # this only rewards having hours data at all over having none.
    return 0.6 if attraction.hours else 0.5


def _score_current_events(attraction: EnrichedAttraction) -> float:
    return 1.0 if attraction.candidate.has_current_event else 0.4


def _score_weather_fit(attraction: EnrichedAttraction, forecast: DayForecast | None) -> float:
    if forecast is None:
        return 0.5
    is_outdoor = any(hint in category.lower() for category in attraction.categories for hint in OUTDOOR_CATEGORY_HINTS)
    if is_bad_weather(forecast):
        return 0.2 if is_outdoor else 1.0
    if is_good_weather(forecast):
        return 1.0 if is_outdoor else 0.6
    return 0.5


def rank_attractions(
    attractions: list[EnrichedAttraction],
    request: DiscoveryRequest,
    interests: list[str],
    forecast: DayForecast | None = None,
) -> list[RankedAttraction]:
    ranked = []
    for attraction in attractions:
        breakdown = {
            "interest_match": round(_score_interest_match(attraction, interests), 4),
            "distance": round(_score_distance(attraction, request), 4),
            "rating": round(_score_rating(attraction), 4),
            "popularity": round(_score_popularity(attraction), 4),
            "price_fit": round(_score_price_fit(attraction, request.max_budget), 4),
            "hours_fit": round(_score_hours_fit(attraction), 4),
            "current_events": round(_score_current_events(attraction), 4),
            "weather_fit": round(_score_weather_fit(attraction, forecast), 4),
        }
        score = round(sum(breakdown[factor] * weight for factor, weight in SCORE_WEIGHTS.items()), 4)
        ranked.append(RankedAttraction(attraction=attraction, score=score, score_breakdown=breakdown))

    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked
