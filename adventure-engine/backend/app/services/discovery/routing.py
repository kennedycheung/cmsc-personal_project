"""Step 8: sequences the final selected attractions into an ordered route
via SerpAPI's Google Maps Directions engine.

That engine is point-to-point only (`start_coords`/`end_coords`, no
multi-stop waypoints in one call), so this chains one call per consecutive
pair of the selected attractions and stitches the legs together, isolating
a failed leg rather than failing the whole route.

Verified against a real API response (not just docs): `directions` is a
flat list of *alternative routes* for the requested travel mode (e.g. 3
different walking routes), each with plain int `distance`
(meters)/`duration` (seconds) fields -- not the nested
`legs[].distance.{text,value}` shape Google's own native Directions API
uses, which is an easy assumption to make wrongly without a live call.
`travel_mode=2` (undocumented in SerpAPI's published params, found by
testing) requests walking-only alternatives, matching this app's existing
walking-route convention (OSRM's foot profile in routing.ts) rather than
mixing in transit/driving options.
"""

from app.services.discovery.serpapi_client import SerpApiError, serpapi_search
from app.services.discovery.types import DiscoveryRoute, EnrichedAttraction, RouteLeg

WALKING_TRAVEL_MODE = 2


def _leg_for_pair(a: EnrichedAttraction, b: EnrichedAttraction) -> RouteLeg | None:
    start_coords = f"{a.candidate.latitude},{a.candidate.longitude}"
    end_coords = f"{b.candidate.latitude},{b.candidate.longitude}"
    try:
        payload = serpapi_search(
            "google_maps_directions",
            {"start_coords": start_coords, "end_coords": end_coords, "travel_mode": WALKING_TRAVEL_MODE},
        )
    except SerpApiError:
        return None

    routes = payload.get("directions") or []
    if not routes:
        return None
    # First alternative is Google's default/best suggestion for the mode.
    route = routes[0]
    duration_seconds = route.get("duration")

    return RouteLeg(
        from_name=a.candidate.name,
        to_name=b.candidate.name,
        distance_text=route.get("formatted_distance"),
        duration_text=route.get("formatted_duration"),
        duration_minutes=(duration_seconds / 60) if duration_seconds else None,
    )


def build_route(selected: list[EnrichedAttraction]) -> DiscoveryRoute | None:
    """Builds a chained route through `selected`, in the given order.
    Returns None for fewer than 2 stops -- there's nothing to route between."""
    if len(selected) < 2:
        return None

    legs = [leg for a, b in zip(selected, selected[1:]) if (leg := _leg_for_pair(a, b)) is not None]
    total_duration = sum(leg.duration_minutes for leg in legs if leg.duration_minutes is not None)
    return DiscoveryRoute(legs=legs, total_duration_minutes=round(total_duration, 1))
