"""Step 3: runs the 4 discovery-search engines (Google Events, Google Maps,
TripAdvisor, Yelp) and normalizes their raw results into a flat list of
RawResult, isolating per-engine failures so one bad/rate-limited engine
doesn't sink the whole discovery request -- same per-source isolation
spirit as deals/pipeline.py's CONNECTORS loop.
"""

from dataclasses import dataclass
from typing import Callable

from app.services.discovery import query_builder
from app.services.discovery.serpapi_client import SerpApiError, serpapi_search
from app.services.discovery.types import DiscoveryRequest, RawResult


def _parse_google_events(payload: dict) -> list[RawResult]:
    # Verified live: `venue` carries no coordinates (only name/rating/reviews),
    # same gap as TripAdvisor/Yelp search results -- merge.py's name-only
    # fallback is what lets these reach a CandidateAttraction at all. The
    # *venue* name (not the specific event's title, e.g. "Baby Wants
    # Candy!") is used as the merge name, since the whole point of this
    # source is tagging an attraction/venue as currently hosting something
    # -- an event title would never fuzzy-match a Google Maps venue listing.
    results = []
    for item in payload.get("events_results", []):
        venue = item.get("venue") or {}
        address = item.get("address")
        results.append(
            RawResult(
                engine="google_events",
                name=venue.get("name") or item.get("title", ""),
                address=address[0] if isinstance(address, list) and address else address,
                latitude=None,
                longitude=None,
                rating=venue.get("rating"),
                review_count=venue.get("reviews"),
                is_event=True,
                event_date=(item.get("date") or {}).get("start_date"),
                raw=item,
            )
        )
    return results


def _parse_google_maps(payload: dict) -> list[RawResult]:
    results = []
    for item in payload.get("local_results", []):
        gps = item.get("gps_coordinates") or {}
        price = item.get("price")
        # `types` (plural) is the richer tag list SerpAPI actually returns
        # (e.g. ["History museum", "Cultural center", "Museum", "Tourist
        # attraction"]); `type` (singular) is just its first entry. Prefer
        # the richer list for interest matching, falling back to `type`
        # only if `types` is absent.
        categories = item.get("types") or ([item["type"]] if item.get("type") else [])
        results.append(
            RawResult(
                engine="google_maps",
                name=item.get("title", ""),
                address=item.get("address"),
                latitude=gps.get("latitude"),
                longitude=gps.get("longitude"),
                external_ids={"google_maps": item["place_id"]} if item.get("place_id") else {},
                rating=item.get("rating"),
                review_count=item.get("reviews"),
                price_level=len(price) if isinstance(price, str) else None,
                categories=categories,
                raw=item,
            )
        )
    return results


def _parse_tripadvisor(payload: dict) -> list[RawResult]:
    # Verified against a real response: search results live under "places"
    # and carry no coordinates at all (only a free-text `location` string) --
    # merge.py falls back to name-only matching for results like this, and
    # drops any that never match a coordinate-bearing result from another
    # engine, since there's nowhere to place them on a map/route.
    results = []
    for item in payload.get("places", []):
        place_type = item.get("place_type")
        results.append(
            RawResult(
                engine="tripadvisor",
                name=item.get("title", ""),
                address=item.get("location"),
                latitude=None,
                longitude=None,
                external_ids={"tripadvisor": str(item["place_id"])} if item.get("place_id") else {},
                rating=item.get("rating"),
                review_count=item.get("reviews"),
                categories=[place_type] if place_type else [],
                raw=item,
            )
        )
    return results


def _parse_yelp(payload: dict) -> list[RawResult]:
    # Verified against a real response: `categories` is a list of {"title":
    # ..., "link": ...} objects, not plain strings, and search results
    # carry no coordinates -- same name-only-merge fallback as TripAdvisor.
    results = []
    for item in payload.get("organic_results", []):
        price = item.get("price")
        categories = [c.get("title") for c in item.get("categories", []) if c.get("title")]
        results.append(
            RawResult(
                engine="yelp",
                name=item.get("title", ""),
                address=item.get("neighborhoods"),
                latitude=None,
                longitude=None,
                external_ids={"yelp": item["place_ids"][0]} if item.get("place_ids") else {},
                rating=item.get("rating"),
                review_count=item.get("reviews"),
                price_level=len(price) if isinstance(price, str) else None,
                categories=categories,
                raw=item,
            )
        )
    return results


@dataclass
class DiscoveryEngineAdapter:
    name: str
    serpapi_engine: str
    build_params: Callable[[DiscoveryRequest, list[str]], dict]
    parse_results: Callable[[dict], list[RawResult]]


# Registry of discovery-search adapters -- adding a future source (Viator,
# GetYourGuide, Ticketmaster, ...) is a new adapter appended here, not a
# change to run_discovery_searches or anything downstream.
DISCOVERY_ENGINES: list[DiscoveryEngineAdapter] = [
    DiscoveryEngineAdapter(
        "google_events", "google_events", query_builder.build_google_events_params, _parse_google_events
    ),
    DiscoveryEngineAdapter(
        "google_maps", "google_maps", query_builder.build_google_maps_params, _parse_google_maps
    ),
    DiscoveryEngineAdapter(
        "tripadvisor", "tripadvisor", query_builder.build_tripadvisor_params, _parse_tripadvisor
    ),
    DiscoveryEngineAdapter("yelp", "yelp", query_builder.build_yelp_params, _parse_yelp),
]


def run_discovery_searches(request: DiscoveryRequest, interests: list[str]) -> tuple[list[RawResult], list[str]]:
    """Runs every registered discovery engine, isolating failures.

    Returns (all raw results, warnings) -- one bad engine adds a warning and
    is skipped rather than failing the whole request.
    """
    all_results: list[RawResult] = []
    warnings: list[str] = []

    for adapter in DISCOVERY_ENGINES:
        params = adapter.build_params(request, interests)
        try:
            payload = serpapi_search(adapter.serpapi_engine, params)
            all_results.extend(adapter.parse_results(payload))
        except SerpApiError as exc:
            warnings.append(f"{adapter.name}: {exc}")

    return all_results, warnings
