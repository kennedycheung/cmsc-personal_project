"""Step 2: builds a distinct, tailored search query per discovery engine --
deliberately not the same search string reused across engines, since each
platform's search semantics/fields differ (free-text `q` vs. split
`find_desc`/`find_loc` fields, coordinate formats, category filters).
"""

from app.services.discovery.types import DiscoveryRequest

_EVENT_HINT_CATEGORIES = {"festivals", "nightlife"}


def _interest_phrase(interests: list[str]) -> str:
    if not interests:
        return "things to do"
    return " and ".join(tag.replace("_", " ") for tag in interests)


def build_google_events_params(request: DiscoveryRequest, interests: list[str]) -> dict:
    params: dict = {
        "q": f"{_interest_phrase(interests)} events in {request.location_label}",
        "location": request.location_label,
    }
    if any(tag in _EVENT_HINT_CATEGORIES for tag in interests):
        params["htichips"] = "date:week"
    return params


def build_google_maps_params(request: DiscoveryRequest, interests: list[str]) -> dict:
    return {
        "q": f"{_interest_phrase(interests)} attractions near {request.location_label}",
        "ll": f"@{request.latitude},{request.longitude},14z",
        "type": "search",
    }


def build_tripadvisor_params(request: DiscoveryRequest, interests: list[str]) -> dict:
    return {
        "q": f"best {_interest_phrase(interests)} in {request.location_label}",
        "ssrc": "A",  # "Things to do" category
        "lat": request.latitude,
        "lon": request.longitude,
    }


def build_yelp_params(request: DiscoveryRequest, interests: list[str]) -> dict:
    return {"find_desc": _interest_phrase(interests), "find_loc": request.location_label}
