"""Step 7: groups the ranked list into the 7 named recommendation buckets.

Deterministic rules over the already-ranked list, not a second scoring
pass -- each bucket picks its top qualifying candidate(s) that haven't
already been used by a higher-priority bucket, so the same attraction
doesn't just show up in every bucket.
"""

from app.services.discovery.ranking import OUTDOOR_CATEGORY_HINTS
from app.services.discovery.types import RankedAttraction, RecommendationBuckets

HIDDEN_GEM_MAX_REVIEWS = 50
HIDDEN_GEM_MIN_RATING = 4.0
BUCKET_SIZE = 3

_EVENING_HINTS = {"nightlife", "bar", "club", "theater", "theatre", "restaurant"}
_FAMILY_HINTS = {"family", "kids", "amusement", "zoo", "aquarium", "park"}


def _tags(ranked: RankedAttraction) -> set[str]:
    return {c.lower() for c in ranked.attraction.categories}


def _is_family(ranked: RankedAttraction) -> bool:
    return bool(_tags(ranked) & _FAMILY_HINTS)


def _is_evening(ranked: RankedAttraction) -> bool:
    return bool(_tags(ranked) & _EVENING_HINTS)


def _is_indoor(ranked: RankedAttraction) -> bool:
    return not bool(_tags(ranked) & OUTDOOR_CATEGORY_HINTS)


def _is_free(ranked: RankedAttraction) -> bool:
    return ranked.attraction.price_level == 0


def _is_hidden_gem(ranked: RankedAttraction) -> bool:
    rating = ranked.attraction.rating or 0
    reviews = ranked.attraction.review_count or 0
    return rating >= HIDDEN_GEM_MIN_RATING and reviews <= HIDDEN_GEM_MAX_REVIEWS


def _value_ratio(ranked: RankedAttraction) -> float:
    price_level = ranked.attraction.price_level
    if not price_level:
        return ranked.score  # free/unknown-price treated as maximal value
    return ranked.score / price_level


def _pick_top(ranked: list[RankedAttraction], predicate, used: set[int], limit: int = BUCKET_SIZE) -> list[RankedAttraction]:
    picks: list[RankedAttraction] = []
    for item in ranked:
        if id(item) in used:
            continue
        if predicate is not None and not predicate(item):
            continue
        picks.append(item)
        used.add(id(item))
        if len(picks) >= limit:
            break
    return picks


def build_recommendation_buckets(ranked: list[RankedAttraction]) -> RecommendationBuckets:
    used: set[int] = set()

    best_overall = _pick_top(ranked, None, used)
    best_value = _pick_top(sorted(ranked, key=_value_ratio, reverse=True), None, used)
    best_hidden_gem = _pick_top(ranked, _is_hidden_gem, used)
    best_family = _pick_top(ranked, _is_family, used)
    best_evening = _pick_top(ranked, _is_evening, used)
    best_rainy_day = _pick_top(ranked, _is_indoor, used)
    best_free = _pick_top(ranked, _is_free, used)

    return RecommendationBuckets(
        best_overall=best_overall,
        best_value=best_value,
        best_hidden_gem=best_hidden_gem,
        best_family=best_family,
        best_evening=best_evening,
        best_rainy_day=best_rainy_day,
        best_free=best_free,
    )
