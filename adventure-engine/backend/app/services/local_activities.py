"""Live, non-persisted discovery of nearby real activities for a "local
adventure" (a trip under a day -- no flights or hotels, see
progressive_recommendation_flow.md). Unlike osm_activities.py's ingestion
pipeline, this queries Overpass around an arbitrary origin point and
returns results directly -- nothing is written to the database, since
there's no seeded Destination row for an arbitrary point to attach to.
"""

from dataclasses import dataclass

from app.services.osm_activities import _OSM_TAGS, OsmIngestionError, fetch_osm_activities, normalize_osm_element_raw

DEFAULT_RADIUS_KM = 15.0
MAX_RESULTS_PER_GROUP = 8

# The 7 groups from the product spec, in display order.
ACTIVITY_GROUPS = ["nature", "food", "culture", "entertainment", "shopping", "outdoor_recreation", "relaxation"]


class LocalActivityDiscoveryError(Exception):
    """Raised when Overpass can't be reached or returns an unusable response."""


@dataclass
class LocalActivity:
    name: str
    description: str | None
    group: str
    category: str
    location: str
    latitude: float
    longitude: float
    distance_km: float
    duration_hours: float
    is_outdoor: bool
    opening_time: str | None
    closing_time: str | None


def discover_local_activities(
    latitude: float,
    longitude: float,
    origin_label: str,
    radius_km: float = DEFAULT_RADIUS_KM,
    groups: list[str] | None = None,
) -> dict[str, list[LocalActivity]]:
    """Returns nearby real activities grouped by category (nature, food,
    culture, entertainment, shopping, outdoor_recreation, relaxation).
    `groups` restricts the search to a subset; omit for all seven. Raises
    LocalActivityDiscoveryError on failure -- callers should surface this
    as a retryable "couldn't reach OpenStreetMap" state rather than
    presenting an empty result as "no activities found nearby".
    """
    requested_groups = set(groups) if groups else set(ACTIVITY_GROUPS)
    tags = {key: info for key, info in _OSM_TAGS.items() if info[0] in requested_groups}

    try:
        elements = fetch_osm_activities(
            latitude, longitude, radius_km=radius_km, tags=tags, result_limit=len(tags) * 4
        )
    except OsmIngestionError as exc:
        raise LocalActivityDiscoveryError(str(exc)) from exc

    grouped: dict[str, list[LocalActivity]] = {group: [] for group in ACTIVITY_GROUPS if group in requested_groups}

    for element in elements:
        normalized = normalize_osm_element_raw(element, latitude, longitude, origin_label)
        if normalized is None:
            continue

        group = normalized["group"]
        if group not in grouped or len(grouped[group]) >= MAX_RESULTS_PER_GROUP:
            continue

        grouped[group].append(
            LocalActivity(
                name=normalized["name"],
                description=normalized["description"],
                group=group,
                category=normalized["category"],
                location=normalized["location"],
                latitude=normalized["latitude"],
                longitude=normalized["longitude"],
                distance_km=normalized["distance_km"],
                duration_hours=normalized["duration_hours"],
                is_outdoor=normalized["is_outdoor"],
                opening_time=normalized["opening_time"],
                closing_time=normalized["closing_time"],
            )
        )

    for group_activities in grouped.values():
        group_activities.sort(key=lambda a: a.distance_km)

    return grouped
