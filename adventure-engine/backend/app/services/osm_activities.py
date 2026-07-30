"""Real, live-sourced activities from OpenStreetMap's Overpass API -- free,
no API key, no signup. Used as an on-demand supplement to the hand-curated
seed activities so a destination's activity pool isn't limited to whatever
was manually typed in ahead of time.

See documentation/osm_activity_ingestion.md for the full write-up.
"""

from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.destination import Destination
from app.services.optimizations.geo import haversine_km

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_TIMEOUT_SECONDS = 40.0
# Overpass's usage policy asks callers to identify themselves with a
# descriptive User-Agent; requests without one have been observed to get
# rejected outright (406) rather than just deprioritized.
REQUEST_HEADERS = {"User-Agent": "adventure-arbitrage-engine/1.0 (portfolio project)"}
DEFAULT_RADIUS_KM = 5
MAX_RESULTS_PER_DESTINATION = 12
ASSUMED_LOCAL_SPEED_KMH = 25.0  # rough in-city travel speed, same spirit as optimizations/constants.py

# OSM tag=value pairs worth surfacing as activities, each mapped to a
# (category, default duration_hours, is_outdoor) triple. Duration and
# is_outdoor are documented assumptions -- OSM doesn't carry either -- same
# as the curated defaults used elsewhere in this app (see
# backpacker_optimizations.md's constants table for the same pattern).
_OSM_TAGS: dict[tuple[str, str], tuple[str, float, bool]] = {
    ("tourism", "museum"): ("culture", 2.0, False),
    ("tourism", "gallery"): ("art", 1.5, False),
    ("tourism", "aquarium"): ("wildlife", 2.0, False),
    ("tourism", "zoo"): ("wildlife", 3.0, True),
    ("tourism", "theme_park"): ("adventure", 4.0, True),
    ("tourism", "viewpoint"): ("scenery", 0.75, True),
    ("tourism", "attraction"): ("sightseeing", 1.5, True),
    ("leisure", "park"): ("relaxation", 1.5, True),
    ("historic", "monument"): ("history", 1.0, True),
    ("historic", "castle"): ("history", 1.5, True),
    ("historic", "ruins"): ("history", 1.0, True),
    ("natural", "beach"): ("relaxation", 2.0, True),
}

_OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:30];
(
{clauses}
);
out center {limit};
"""


class OsmIngestionError(Exception):
    """Raised when Overpass can't be reached or returns an unusable response."""


@dataclass
class OsmIngestionSummary:
    inserted: int = 0
    updated: int = 0
    skipped_unnamed: int = 0
    errors: list[str] = field(default_factory=list)
    by_destination: dict[str, int] = field(default_factory=dict)


def _build_query(latitude: float, longitude: float, radius_km: float) -> str:
    radius_m = int(radius_km * 1000)
    around = f"around:{radius_m},{latitude},{longitude}"
    clauses = "\n".join(
        f'  node["{key}"="{value}"]({around});' for key, value in _OSM_TAGS
    )
    return _OVERPASS_QUERY_TEMPLATE.format(clauses=clauses, limit=MAX_RESULTS_PER_DESTINATION * 3)


def _parse_simple_opening_hours(raw: str | None) -> tuple[str | None, str | None]:
    """Best-effort parse of the common "Hh:MM-Hh:MM" OSM opening_hours shape.

    OSM's opening_hours syntax supports a much richer grammar (day ranges,
    multiple shifts, holidays, etc.) that isn't worth fully implementing
    here -- anything more complex than a single "HH:MM-HH:MM" span is left
    as (None, None), which the itinerary scheduler already treats as "open
    all day" rather than guessing wrong.
    """
    if not raw or "-" not in raw or "," in raw or ";" in raw:
        return None, None
    start, _, end = raw.partition("-")
    start, end = start.strip(), end.strip()
    if len(start) == 5 and len(end) == 5 and start[2] == ":" and end[2] == ":":
        return start, end
    return None, None


def fetch_osm_activities(latitude: float, longitude: float, radius_km: float = DEFAULT_RADIUS_KM) -> list[dict]:
    """Fetch nearby real POIs from Overpass. Raises OsmIngestionError on any
    network/parse failure -- callers should treat this the same way the rest
    of this app treats a flaky third-party API (skip, don't crash)."""
    try:
        # POST, not GET: Overpass's own docs recommend this for anything
        # beyond a trivial query -- a GET with this much query data in the
        # URL gets rejected outright (observed 406 Not Acceptable in testing).
        response = httpx.post(
            OVERPASS_URL,
            data={"data": _build_query(latitude, longitude, radius_km)},
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["elements"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise OsmIngestionError(str(exc)) from exc


def normalize_osm_element(element: dict, destination: Destination) -> dict[str, Any] | None:
    """Maps one raw Overpass element onto Activity fields. Returns None for
    elements that can't produce a presentable activity (no name -- most
    commonly unnamed benches/minor nodes that happen to carry a matched
    tag)."""
    tags = element.get("tags", {})
    name = tags.get("name")
    if not name:
        return None

    category, default_duration, default_outdoor = next(
        (
            info
            for (key, value), info in _OSM_TAGS.items()
            if tags.get(key) == value
        ),
        ("sightseeing", 1.0, True),
    )

    lat = element.get("lat")
    lon = element.get("lon")
    if lat is None or lon is None:
        return None

    distance_km = haversine_km(destination.latitude, destination.longitude, lat, lon)
    travel_minutes = round((distance_km / ASSUMED_LOCAL_SPEED_KMH) * 60, 1)

    opening_time, closing_time = _parse_simple_opening_hours(tags.get("opening_hours"))

    return {
        "source": "osm",
        "external_id": f"{element['type']}/{element['id']}",
        "name": name,
        "description": tags.get("description"),
        "category": category,
        # OSM doesn't carry pricing -- 0/unknown, the same honest gap as
        # the deal connectors' placeholder data (see
        # deal_ingestion_pipeline.md). Free real attractions (parks,
        # viewpoints, monuments) are frequently actually free, so this
        # isn't always wrong, but it's not verified either.
        "price": 0.0,
        "duration_hours": default_duration,
        "location": tags.get("addr:suburb") or tags.get("addr:city") or destination.name,
        "opening_time": opening_time,
        "closing_time": closing_time,
        "travel_minutes": travel_minutes,
        "latitude": lat,
        "longitude": lon,
        "is_outdoor": default_outdoor,
    }


def ingest_osm_activities_for_destination(
    db: Session, destination: Destination, radius_km: float = DEFAULT_RADIUS_KM
) -> OsmIngestionSummary:
    summary = OsmIngestionSummary()

    try:
        elements = fetch_osm_activities(destination.latitude, destination.longitude, radius_km)
    except OsmIngestionError as exc:
        summary.errors.append(f"{destination.name}: {exc}")
        summary.by_destination[destination.name] = 0
        return summary

    processed = 0
    for element in elements:
        if processed >= MAX_RESULTS_PER_DESTINATION:
            break

        normalized = normalize_osm_element(element, destination)
        if normalized is None:
            summary.skipped_unnamed += 1
            continue

        existing = db.execute(
            select(Activity).where(
                Activity.source == normalized["source"], Activity.external_id == normalized["external_id"]
            )
        ).scalar_one_or_none()

        if existing is not None:
            for field_name, value in normalized.items():
                setattr(existing, field_name, value)
            summary.updated += 1
        else:
            db.add(Activity(**normalized, destination_id=destination.id))
            summary.inserted += 1

        processed += 1

    summary.by_destination[destination.name] = processed
    db.commit()
    return summary


def ingest_osm_activities(db: Session, destination_id: int | None = None) -> OsmIngestionSummary:
    """Runs OSM ingestion for one destination, or every destination if
    destination_id is omitted. Deliberately not run automatically on
    backend startup (unlike the deal pipeline): Overpass is a real, shared
    public service with a fair-use policy, and re-querying it for every
    seeded destination on every dev restart would be an unfriendly amount
    of load for a service this app doesn't own. Trigger via
    POST /api/activities/ingest-osm instead.
    """
    if destination_id is not None:
        destination = db.get(Destination, destination_id)
        if destination is None:
            raise ValueError(f"Destination {destination_id} not found")
        return ingest_osm_activities_for_destination(db, destination)

    combined = OsmIngestionSummary()
    destinations = list(db.execute(select(Destination)).scalars().all())
    for destination in destinations:
        result = ingest_osm_activities_for_destination(db, destination)
        combined.inserted += result.inserted
        combined.updated += result.updated
        combined.skipped_unnamed += result.skipped_unnamed
        combined.errors.extend(result.errors)
        combined.by_destination.update(result.by_destination)

    return combined
