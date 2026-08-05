"""Low-level SerpAPI HTTP client shared by every discovery-engine adapter.

SerpAPI is a paid, keyed service (unlike every other external API this app
uses -- Open-Meteo, OSM/Overpass, OSRM, Nominatim, Frankfurter are all free
and keyless) that proxies Google/TripAdvisor/Yelp search results across
distinct "engines" (one per source/purpose). See
documentation/activity_discovery_engine.md for the full engine map.
"""

import time

import httpx

from app.core.config import settings

SERPAPI_BASE_URL = "https://serpapi.com/search"
REQUEST_TIMEOUT_SECONDS = 15.0
# SerpAPI bills per search, so caching identical repeat requests (e.g. the
# same city/interest searched again shortly after) is the primary cost
# control here -- same in-memory TTL-cache idiom as weather.py/geocoding.py.
CACHE_TTL_SECONDS = 1800

_cache: dict[tuple, tuple[float, dict]] = {}


class SerpApiError(Exception):
    """Raised when SerpAPI can't be reached or returns an unusable response."""


class SerpApiNotConfiguredError(SerpApiError):
    """Raised when no SERPAPI_KEY is set -- distinct from a network/API failure."""


def _cache_key(engine: str, params: dict) -> tuple:
    return (engine, tuple(sorted((k, str(v)) for k, v in params.items())))


def serpapi_search(engine: str, params: dict) -> dict:
    """Calls one SerpAPI engine (e.g. "google_events", "yelp_place") and
    returns its parsed JSON response.

    Raises SerpApiNotConfiguredError if no key is set, or SerpApiError on
    any network/parse failure or an API-reported error -- callers (see
    search_engines.py/enrichment.py) isolate this per engine rather than
    letting one failing engine sink the whole discovery request.
    """
    if not settings.serpapi_key:
        raise SerpApiNotConfiguredError("SERPAPI_KEY is not configured")

    key = _cache_key(engine, params)
    cached = _cache.get(key)
    if cached is not None and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        response = httpx.get(
            SERPAPI_BASE_URL,
            params={**params, "engine": engine, "api_key": settings.serpapi_key},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise SerpApiError(f"{engine}: {exc}") from exc

    if isinstance(payload, dict) and payload.get("error"):
        raise SerpApiError(f"{engine}: {payload['error']}")

    _cache[key] = (time.monotonic(), payload)
    return payload
