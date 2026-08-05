"""Top-level orchestrator for the adventure recommendation engine.

Pipeline: Location Resolution (caller-provided, already geocoded via
services/geocoding.py) -> Candidate Generation + Nearby Attraction
Discovery (real OSM data via local_activities.py) -> Activity Clustering
-> Scoring -> Ranking -> Recommendation Generation (with reasoning) ->
Itinerary Generation.

See documentation/adventure_recommendation_engine.md for the full write-up.
Uses only OpenStreetMap/Nominatim/Overpass and this app's existing
Open-Meteo weather integration -- no paid/keyed API is required for this
engine to work, by design (see providers.py for the future-integration
points that stay disabled until credentials exist).
"""

from app.services.adventure_engine.clustering import cluster_activities
from app.services.adventure_engine.itinerary import build_itinerary
from app.services.adventure_engine.reasoning import build_summary
from app.services.adventure_engine.scoring import score_cluster
from app.services.adventure_engine.types import AdventureRecommendation, AdventureRequest
from app.services.local_activities import LocalActivityDiscoveryError, discover_local_activities
from app.services.weather import DayForecast, WeatherUnavailableError, get_forecast

MAX_RECOMMENDATIONS = 10


def recommend_adventures(request: AdventureRequest) -> tuple[list[AdventureRecommendation], list[str]]:
    warnings: list[str] = []

    try:
        grouped = discover_local_activities(
            request.latitude, request.longitude, request.location_label, radius_km=request.radius_km
        )
    except LocalActivityDiscoveryError as exc:
        return [], [f"Could not reach OpenStreetMap: {exc}"]

    all_activities = [activity for group_activities in grouped.values() for activity in group_activities]
    if not all_activities:
        return [], ["No nearby activities found for this location and radius."]

    forecast: DayForecast | None = None
    try:
        forecast_list = get_forecast(request.latitude, request.longitude, 1)
        forecast = forecast_list[0] if forecast_list else None
    except WeatherUnavailableError:
        warnings.append("Weather forecast unavailable; scoring did not account for weather.")

    clusters = cluster_activities(all_activities)

    recommendations: list[AdventureRecommendation] = []
    for cluster in clusters:
        total_score, confidence, reasons = score_cluster(cluster, request, forecast)
        summary = build_summary(reasons, request.location_label)
        itinerary = build_itinerary(cluster) if len(cluster.activities) > 1 else None
        recommendations.append(
            AdventureRecommendation(
                location_label=request.location_label,
                latitude=cluster.center_lat,
                longitude=cluster.center_lon,
                total_score=total_score,
                confidence=confidence,
                reasons=reasons,
                summary=summary,
                activities=cluster.activities,
                itinerary=itinerary,
            )
        )

    recommendations.sort(key=lambda r: r.total_score, reverse=True)
    return recommendations[:MAX_RECOMMENDATIONS], warnings
