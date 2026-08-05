"""Step 4: fuzzy-merges near-duplicate results from different engines into
one CandidateAttraction each -- e.g. "Senso-ji" (one engine) and "Sensoji
Temple" (another) collapse into a single attraction rather than showing up
twice.

Two results are treated as the same place if they're within a tight
distance regardless of name (the same coordinates, wildly different name
transliteration), or within a looser distance *and* their names are similar
enough by rapidfuzz. All thresholds are documented assumptions, same spirit
as the weight/threshold tables elsewhere in this app (e.g. itinerary.py's
SCORE_WEIGHTS, osm_activities.py's _OSM_TAGS).

Verified against real responses: TripAdvisor's and Yelp's *search*-tier
results (as opposed to their Place/Details endpoints) carry no coordinates
at all, only a free-text location string. Refusing to merge anything
without coordinates would silently drop every TripAdvisor/Yelp result, so
name-similarity alone is used as a fallback whenever either side lacks
coordinates -- accepting a small risk of merging two different same-named
venues (bounded somewhat by every search already being scoped to one city)
in exchange for actually surfacing these sources at all. A cluster that
never picks up a coordinate from *any* member (e.g. a TripAdvisor/Yelp find
with no matching Google Maps result) is dropped entirely in
merge_candidates -- there's nowhere to place it on a map or route.
"""

from rapidfuzz import fuzz

from app.services.discovery.types import CandidateAttraction, RawResult
from app.services.optimizations.geo import haversine_km

TIGHT_MATCH_DISTANCE_KM = 0.05  # 50m -- treat as the same place regardless of name
LOOSE_MATCH_DISTANCE_KM = 0.15  # 150m -- only merge if the name also matches
NAME_SIMILARITY_THRESHOLD = 80  # rapidfuzz token_sort_ratio, 0-100


def _same_place(a: RawResult, b: RawResult) -> bool:
    has_coords = (
        a.latitude is not None and a.longitude is not None and b.latitude is not None and b.longitude is not None
    )
    if not has_coords:
        return fuzz.token_sort_ratio(a.name, b.name) >= NAME_SIMILARITY_THRESHOLD

    distance_km = haversine_km(a.latitude, a.longitude, b.latitude, b.longitude)
    if distance_km <= TIGHT_MATCH_DISTANCE_KM:
        return True
    if distance_km <= LOOSE_MATCH_DISTANCE_KM:
        return fuzz.token_sort_ratio(a.name, b.name) >= NAME_SIMILARITY_THRESHOLD
    return False


def merge_candidates(results: list[RawResult]) -> list[CandidateAttraction]:
    usable = [r for r in results if r.name]

    clusters: list[list[RawResult]] = []
    for result in usable:
        placed = False
        for cluster in clusters:
            if any(_same_place(result, existing) for existing in cluster):
                cluster.append(result)
                placed = True
                break
        if not placed:
            clusters.append([result])

    candidates: list[CandidateAttraction] = []
    for cluster in clusters:
        coords = [(r.latitude, r.longitude) for r in cluster if r.latitude is not None and r.longitude is not None]
        if not coords:
            continue  # no member of this cluster has a position -- can't place it

        # Prefer the longest name as the display name -- usually the most
        # descriptive one (e.g. "Sensoji Temple" over "Senso-ji").
        best = max(cluster, key=lambda r: len(r.name))

        external_ids: dict[str, str] = {}
        categories: list[str] = []
        for item in cluster:
            external_ids.update(item.external_ids)
            categories.extend(c for c in item.categories if c not in categories)

        ratings = [r.rating for r in cluster if r.rating is not None]
        review_counts = [r.review_count for r in cluster if r.review_count is not None]

        candidates.append(
            CandidateAttraction(
                name=best.name,
                address=next((r.address for r in cluster if r.address), None),
                latitude=sum(c[0] for c in coords) / len(coords),
                longitude=sum(c[1] for c in coords) / len(coords),
                external_ids=external_ids,
                engines={r.engine for r in cluster},
                sources=cluster,
                rating=round(sum(ratings) / len(ratings), 2) if ratings else None,
                review_count=max(review_counts) if review_counts else None,
                price_level=next((r.price_level for r in cluster if r.price_level is not None), None),
                categories=categories,
                has_current_event=any(r.is_event for r in cluster),
            )
        )

    return candidates
