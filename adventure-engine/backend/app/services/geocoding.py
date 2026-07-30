"""Nominatim geocoding client: free, no API key, used to resolve a
traveler's free-text starting location (a city or an airport name) into
coordinates for distance-constrained recommendations.

See documentation/progressive_recommendation_flow.md for the full write-up.
"""

import time
from dataclasses import dataclass

import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT_SECONDS = 10.0
CACHE_TTL_SECONDS = 3600  # a place's coordinates don't change; cache generously.
# Nominatim's usage policy asks for a descriptive User-Agent and no more
# than one request per second from a single client -- both enforced below,
# the same pattern already used for Overpass (see osm_activities.py).
REQUEST_HEADERS = {"User-Agent": "adventure-arbitrage-engine/1.0 (portfolio project)"}
MIN_SECONDS_BETWEEN_REQUESTS = 1.0

_last_request_at: float = 0.0
_cache: dict[str, tuple[float, "GeocodeResult"]] = {}


@dataclass
class GeocodeResult:
    latitude: float
    longitude: float
    label: str
    country: str | None


class GeocodeError(Exception):
    """Raised when Nominatim can't be reached, or the query matches nothing."""


def _throttle() -> None:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < MIN_SECONDS_BETWEEN_REQUESTS:
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS - elapsed)
    _last_request_at = time.monotonic()


def geocode(query: str) -> GeocodeResult:
    """Resolve a free-text location (city name, airport name/code) to
    coordinates. Raises GeocodeError on any network failure or a query that
    matches nothing -- callers should surface this as "location not found"
    rather than silently guessing.
    """
    normalized_query = query.strip()
    if not normalized_query:
        raise GeocodeError("Empty query")

    cache_key = normalized_query.lower()
    cached = _cache.get(cache_key)
    if cached is not None and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    _throttle()

    try:
        response = httpx.get(
            NOMINATIM_URL,
            params={
                "q": normalized_query,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
            },
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise GeocodeError(str(exc)) from exc

    if not results:
        raise GeocodeError(f"No location found matching {normalized_query!r}")

    top = results[0]
    try:
        result = GeocodeResult(
            latitude=float(top["lat"]),
            longitude=float(top["lon"]),
            label=top.get("display_name", normalized_query),
            country=(top.get("address") or {}).get("country"),
        )
    except (KeyError, ValueError) as exc:
        raise GeocodeError(str(exc)) from exc

    _cache[cache_key] = (time.monotonic(), result)
    return result
