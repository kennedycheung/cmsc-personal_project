"""Top-level orchestrator wiring the Activity Discovery Engine's 8 steps
together. See documentation/activity_discovery_engine.md.
"""

from app.core.config import settings
from app.services.discovery.buckets import build_recommendation_buckets
from app.services.discovery.enrichment import enrich_candidates
from app.services.discovery.interests import classify_interests
from app.services.discovery.merge import merge_candidates
from app.services.discovery.ranking import rank_attractions
from app.services.discovery.routing import build_route
from app.services.discovery.search_engines import run_discovery_searches
from app.services.discovery.serpapi_client import SerpApiNotConfiguredError
from app.services.discovery.types import DiscoveryRequest, DiscoveryResult
from app.services.weather import WeatherUnavailableError, get_forecast


def discover(request: DiscoveryRequest) -> DiscoveryResult:
    """Runs Steps 1-8 in order. Raises SerpApiNotConfiguredError up front
    (before spending any calls) if SERPAPI_KEY isn't set -- callers (see
    api/routes/discovery.py) turn that into a clear 503 rather than a
    confusing all-warnings empty result."""
    if not settings.serpapi_key:
        raise SerpApiNotConfiguredError("SERPAPI_KEY is not configured")

    warnings: list[str] = []

    interests = classify_interests(request.free_text, request.interests)

    raw_results, search_warnings = run_discovery_searches(request, interests)
    warnings.extend(search_warnings)

    candidates = merge_candidates(raw_results)
    enriched, enrich_warnings = enrich_candidates(candidates)
    warnings.extend(enrich_warnings)

    try:
        forecast = get_forecast(request.latitude, request.longitude, 1)
        today_forecast = forecast[0] if forecast else None
    except WeatherUnavailableError:
        today_forecast = None
        warnings.append("Weather forecast unavailable; ranking did not account for weather.")

    ranked = rank_attractions(enriched, request, interests, today_forecast)
    buckets = build_recommendation_buckets(ranked)

    # Step 8 only makes sense once attractions have actually been selected --
    # "Best Overall" is the natural stand-in for "what the user picked" here,
    # since this standalone endpoint has no separate selection step of its own.
    selected = [r.attraction for r in buckets.best_overall]
    route = build_route(selected)

    return DiscoveryResult(buckets=buckets, route=route, warnings=warnings)
