"""Modular, independent scoring components for ranking candidate adventure
clusters -- each factor is a pure function `(cluster, request, ...) ->
ScoreReason` that also produces a human-readable, template-generated
explanation (never fabricated/LLM text, same "real data or honest local
math" principle as every other scoring function in this app). Adding a new
factor means adding one function and one line in SCORE_WEIGHTS/SCORERS,
not touching engine.py's orchestration.

See documentation/adventure_recommendation_engine.md for the full write-up
of each factor and the reasoning behind the weights.
"""

from app.services.adventure_engine.types import AdventureCluster, AdventureRequest, ScoreReason
from app.services.local_activities import ACTIVITY_GROUPS
from app.services.optimizations.geo import haversine_km
from app.services.weather import DayForecast, is_bad_weather, is_good_weather

SCORE_WEIGHTS: dict[str, float] = {
    "distance": 0.15,
    "density": 0.20,
    "diversity": 0.15,
    "walkability": 0.15,
    "interest_match": 0.15,
    "budget_fit": 0.05,
    "weather_fit": 0.10,
    "confidence": 0.05,
}

MAX_RELEVANT_DISTANCE_KM = 20.0
DENSITY_REFERENCE_COUNT = 6  # cluster size treated as "maximally dense"
# Real walking-route distance would need an OSRM call per candidate cluster
# (expensive at ranking scale, dozens of clusters per request) -- this is a
# documented-assumption average walking speed instead, same spirit as
# osm_activities.py's ASSUMED_LOCAL_SPEED_KMH. Only the final, already-
# selected recommendation needs a real route (see itinerary.py in this
# package, and the existing frontend OSRM integration).
WALKING_SPEED_KMH = 4.8
WALKABILITY_REFERENCE_KM = 0.4  # average inter-stop spacing treated as "very walkable"

_OUTDOOR_GROUPS = {"nature", "outdoor_recreation"}


def _score_distance(cluster: AdventureCluster, request: AdventureRequest) -> ScoreReason:
    distance_km = haversine_km(request.latitude, request.longitude, cluster.center_lat, cluster.center_lon)
    score = max(0.0, 1.0 - distance_km / MAX_RELEVANT_DISTANCE_KM)
    return ScoreReason(
        "distance", round(score, 4), SCORE_WEIGHTS["distance"], f"{distance_km:.1f}km from your starting point"
    )


def _score_density(cluster: AdventureCluster) -> ScoreReason:
    count = len(cluster.activities)
    score = min(1.0, count / DENSITY_REFERENCE_COUNT)
    return ScoreReason(
        "density",
        round(score, 4),
        SCORE_WEIGHTS["density"],
        f"{count} attraction{'s' if count != 1 else ''} clustered together" if count > 1 else "A single standout attraction",
    )


def _score_diversity(cluster: AdventureCluster) -> ScoreReason:
    score = min(1.0, len(cluster.groups) / len(ACTIVITY_GROUPS))
    groups_text = ", ".join(sorted(cluster.groups))
    return ScoreReason(
        "diversity", round(score, 4), SCORE_WEIGHTS["diversity"], f"Spans {len(cluster.groups)} categories: {groups_text}"
    )


def _score_walkability(cluster: AdventureCluster) -> ScoreReason:
    activities = cluster.activities
    if len(activities) < 2:
        return ScoreReason("walkability", 0.5, SCORE_WEIGHTS["walkability"], "Only one stop -- nothing to walk between")

    pairs = 0
    total_km = 0.0
    for i, a in enumerate(activities):
        for b in activities[i + 1 :]:
            total_km += haversine_km(a.latitude, a.longitude, b.latitude, b.longitude)
            pairs += 1
    avg_km = total_km / pairs if pairs else 0.0
    score = max(0.0, 1.0 - avg_km / (WALKABILITY_REFERENCE_KM * 4))
    avg_minutes = (avg_km / WALKING_SPEED_KMH) * 60
    return ScoreReason(
        "walkability",
        round(score, 4),
        SCORE_WEIGHTS["walkability"],
        f"Stops average ~{avg_minutes:.0f} min apart on foot",
    )


def _score_interest_match(cluster: AdventureCluster, request: AdventureRequest) -> ScoreReason:
    if not request.interests:
        return ScoreReason("interest_match", 0.5, SCORE_WEIGHTS["interest_match"], "No specific interests requested")

    requested = {tag.strip().lower() for tag in request.interests if tag.strip()}
    cluster_tags = {g.lower() for g in cluster.groups} | {c.lower() for c in cluster.categories}
    matches = requested & cluster_tags
    score = min(1.0, len(matches) / len(requested)) if requested else 0.5
    reason = (
        f"Matches {len(matches)}/{len(requested)} requested interest(s): {', '.join(sorted(matches))}"
        if matches
        else "Doesn't match your requested interests"
    )
    return ScoreReason("interest_match", round(score, 4), SCORE_WEIGHTS["interest_match"], reason)


def _score_budget_fit(cluster: AdventureCluster, request: AdventureRequest) -> ScoreReason:
    # OpenStreetMap carries no real pricing data -- rather than fabricate a
    # dollar estimate, this factor stays neutral and says so explicitly,
    # the same honest gap documented for deal ingestion and OSM activities
    # elsewhere in this app.
    return ScoreReason(
        "budget_fit",
        0.5,
        SCORE_WEIGHTS["budget_fit"],
        "Real pricing isn't available from OpenStreetMap; scored neutrally rather than guessed",
    )


def _score_weather_fit(cluster: AdventureCluster, forecast: DayForecast | None) -> ScoreReason:
    if forecast is None:
        return ScoreReason("weather_fit", 0.5, SCORE_WEIGHTS["weather_fit"], "No weather forecast available")

    outdoor_share = sum(1 for a in cluster.activities if a.is_outdoor) / len(cluster.activities)
    if is_bad_weather(forecast):
        score = 1.0 - outdoor_share
        reason = f"{forecast.condition.lower()} expected -- {outdoor_share:.0%} of stops are outdoor"
    elif is_good_weather(forecast):
        score = 0.6 + 0.4 * outdoor_share
        reason = f"{forecast.condition.lower()} expected -- good conditions to be outdoors"
    else:
        score = 0.5
        reason = f"{forecast.condition.lower()} expected"
    return ScoreReason("weather_fit", round(max(0.0, min(1.0, score)), 4), SCORE_WEIGHTS["weather_fit"], reason)


def _score_confidence(cluster: AdventureCluster) -> ScoreReason:
    activities = cluster.activities
    with_description = sum(1 for a in activities if a.description)
    with_hours = sum(1 for a in activities if a.opening_time or a.closing_time)
    with_address = sum(1 for a in activities if a.location)
    completeness = (with_description + with_hours + with_address) / (3 * len(activities))
    return ScoreReason(
        "confidence",
        round(completeness, 4),
        SCORE_WEIGHTS["confidence"],
        f"{completeness:.0%} of stops have full details (description, hours, address) from OpenStreetMap",
    )


def score_cluster(
    cluster: AdventureCluster, request: AdventureRequest, forecast: DayForecast | None = None
) -> tuple[float, float, list[ScoreReason]]:
    """Returns (total_score, confidence, reasons). `confidence` is lifted
    out of `reasons` separately since it's also surfaced as its own field
    on AdventureRecommendation (see engine.py), not just folded into the
    weighted total."""
    reasons = [
        _score_distance(cluster, request),
        _score_density(cluster),
        _score_diversity(cluster),
        _score_walkability(cluster),
        _score_interest_match(cluster, request),
        _score_budget_fit(cluster, request),
        _score_weather_fit(cluster, forecast),
        _score_confidence(cluster),
    ]
    total_score = round(sum(r.score * r.weight for r in reasons), 4)
    confidence = next(r.score for r in reasons if r.factor == "confidence")
    return total_score, confidence, reasons
