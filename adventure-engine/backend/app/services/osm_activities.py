"""Real, live-sourced activities from OpenStreetMap's Overpass API -- free,
no API key, no signup. Used as an on-demand supplement to the hand-curated
seed activities so a destination's activity pool isn't limited to whatever
was manually typed in ahead of time.

See documentation/osm_activity_ingestion.md for the full write-up.
"""

import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.destination import Destination
from app.services.optimizations.geo import haversine_km

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_TIMEOUT_SECONDS = 65.0  # must exceed the query's internal [timeout:55] plus network overhead
# Overpass's usage policy asks callers to identify themselves with a
# descriptive User-Agent; requests without one have been observed to get
# rejected outright (406) rather than just deprioritized.
REQUEST_HEADERS = {"User-Agent": "adventure-arbitrage-engine/1.0 (portfolio project)"}
DEFAULT_RADIUS_KM = 12
MAX_RESULTS_PER_DESTINATION = 100
ASSUMED_LOCAL_SPEED_KMH = 25.0  # rough in-city travel speed, same spirit as optimizations/constants.py

# Overpass's free public instance is a shared community resource: bursts of
# testing/usage from one IP routinely trip its own rate limiting (429) or
# leave it briefly overloaded (504), even though the query itself is fine
# (observed repeatedly during development). One retry with a short backoff
# smooths over exactly that transient case without hammering it further --
# deliberately not more than one, since aggressive retrying is the opposite
# of respecting a fair-use limit.
TRANSIENT_STATUS_CODES = {429, 502, 503, 504}
RETRY_BACKOFF_SECONDS = 3.0

# OSM tag=value pairs worth surfacing as activities, each mapped to a
# (group, category, default duration_hours, is_outdoor) tuple. `group` is
# the broader grouping used by local-adventure discovery (see
# local_activities.py); `category` is the finer label stored on Activity
# rows. Duration and is_outdoor are documented assumptions -- OSM doesn't
# carry either -- same as the curated defaults used elsewhere in this app
# (see backpacker_optimizations.md's constants table for the same pattern).
#
# Deliberately excluded: anything that's fundamentally a live event rather
# than a permanent place (concerts, festivals, sporting events, seasonal/
# holiday events) -- OSM models venues (stadiums, theatres), not what's
# scheduled there on a given date. Real event listings need a keyed API
# (Ticketmaster/Eventbrite); see progressive_recommendation_flow.md. Also
# excluded: features that are typically ways/ways/relations without a
# useful single representative point for a huge search radius (forests,
# rivers, general "scenic drives"), and food trucks (too transient to be
# meaningfully tagged in OSM).
_OSM_TAGS: dict[tuple[str, str], tuple[str, str, float, bool]] = {
    # Nature
    ("natural", "beach"): ("nature", "beach", 2.0, True),
    ("natural", "water"): ("nature", "lake", 1.5, True),
    ("waterway", "waterfall"): ("nature", "waterfall", 0.75, True),
    ("tourism", "viewpoint"): ("nature", "viewpoint", 0.75, True),
    ("tourism", "camp_site"): ("nature", "camping", 4.0, True),
    ("leisure", "nature_reserve"): ("nature", "wildlife_refuge", 2.5, True),
    ("boundary", "national_park"): ("nature", "national_park", 4.0, True),
    ("leisure", "garden"): ("nature", "botanical_garden", 1.5, True),
    # Food
    ("amenity", "cafe"): ("food", "cafe", 1.0, False),
    ("shop", "bakery"): ("food", "bakery", 0.5, False),
    ("amenity", "restaurant"): ("food", "restaurant", 1.5, False),
    ("amenity", "food_court"): ("food", "food_hall", 1.0, False),
    ("craft", "brewery"): ("food", "brewery", 1.5, False),
    ("craft", "winery"): ("food", "winery", 1.5, False),
    # Culture
    ("tourism", "museum"): ("culture", "museum", 2.0, False),
    ("tourism", "gallery"): ("culture", "gallery", 1.5, False),
    ("tourism", "attraction"): ("culture", "landmark", 1.5, True),
    ("amenity", "library"): ("culture", "library", 1.0, False),
    ("amenity", "place_of_worship"): ("culture", "landmark", 0.75, False),
    ("man_made", "tower"): ("culture", "landmark", 0.5, True),
    ("historic", "monument"): ("culture", "historic_site", 1.0, True),
    ("historic", "castle"): ("culture", "historic_site", 1.5, True),
    ("historic", "ruins"): ("culture", "historic_site", 1.0, True),
    ("historic", "archaeological_site"): ("culture", "historic_site", 1.0, True),
    # Entertainment (permanent venues only -- see module docstring)
    ("amenity", "theatre"): ("entertainment", "theater", 2.5, False),
    ("amenity", "cinema"): ("entertainment", "cinema", 2.5, False),
    ("amenity", "nightclub"): ("entertainment", "nightlife", 3.0, False),
    ("leisure", "escape_game"): ("entertainment", "escape_room", 1.0, False),
    ("leisure", "amusement_arcade"): ("entertainment", "arcade", 1.5, False),
    ("leisure", "stadium"): ("entertainment", "sports_venue", 3.0, True),
    # Shopping
    ("shop", "antiques"): ("shopping", "antiques", 1.0, False),
    ("shop", "mall"): ("shopping", "mall", 2.0, False),
    ("shop", "department_store"): ("shopping", "department_store", 1.5, False),
    ("shop", "gift"): ("shopping", "souvenir_shop", 0.5, False),
    ("shop", "books"): ("shopping", "bookstore", 0.75, False),
    ("amenity", "marketplace"): ("shopping", "market", 1.5, True),
    # Outdoor recreation
    ("leisure", "slipway"): ("outdoor_recreation", "kayak_paddleboard", 2.0, True),
    ("piste:type", "downhill"): ("outdoor_recreation", "skiing", 4.0, True),
    ("amenity", "bicycle_rental"): ("outdoor_recreation", "cycling", 2.0, True),
    ("sport", "climbing"): ("outdoor_recreation", "climbing", 2.0, True),
    # Relaxation
    ("amenity", "spa"): ("relaxation", "spa", 1.5, False),
    ("natural", "hot_spring"): ("relaxation", "hot_spring", 1.5, True),
    ("tourism", "picnic_site"): ("relaxation", "picnic", 1.5, True),
    ("leisure", "park"): ("relaxation", "park", 1.5, True),
}

_OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:55];
(
{clauses}
);
out center {limit};
"""

# Tags that are commonly mapped as ways/relations (a park boundary, a lake
# shoreline, a national park perimeter) rather than a single point, so they
# need the more expensive "nwr" (node+way+relation) selector to resolve at
# all. Querying "nwr" for *every* tag was tried first and made the combined
# query too expensive for Overpass's own timeout to reliably finish on a
# 12km radius across ~40 tag clauses (observed empty/truncated results,
# taking 50+ seconds, with no error raised since Overpass still returned a
# 200). Keeping the rest on the much cheaper plain "node" selector -- true
# for the large majority of these tags (cafes, shops, museums, viewpoints,
# etc. are almost always mapped as a single point) -- keeps the query fast
# without losing the area-feature coverage that motivated "nwr" in the
# first place.
_NWR_TAGS: set[tuple[str, str]] = {
    ("leisure", "park"),
    ("leisure", "nature_reserve"),
    ("leisure", "garden"),
    ("boundary", "national_park"),
    ("natural", "water"),
    ("tourism", "camp_site"),
    ("leisure", "stadium"),
    ("shop", "mall"),
}


class OsmIngestionError(Exception):
    """Raised when Overpass can't be reached or returns an unusable response."""


@dataclass
class OsmIngestionSummary:
    inserted: int = 0
    updated: int = 0
    skipped_unnamed: int = 0
    errors: list[str] = field(default_factory=list)
    by_destination: dict[str, int] = field(default_factory=dict)


def _build_query(
    latitude: float,
    longitude: float,
    radius_km: float,
    tags: dict[tuple[str, str], tuple[str, str, float, bool]],
    result_limit: int,
) -> str:
    radius_m = int(radius_km * 1000)
    around = f"around:{radius_m},{latitude},{longitude}"
    clauses = "\n".join(
        f'  {"nwr" if (key, value) in _NWR_TAGS else "node"}["{key}"="{value}"]({around});'
        for key, value in tags
    )
    return _OVERPASS_QUERY_TEMPLATE.format(clauses=clauses, limit=result_limit)


def _build_address(tags: dict, fallback_location: str) -> str:
    """Real street address from OSM's addr:* tags when present. Many POIs
    (especially natural features -- beaches, viewpoints, parks) never get a
    full address in OSM; falling back to the neighborhood/city/origin label
    in that case is honest, not a fabricated address standing in for one
    that doesn't exist.
    """
    street = tags.get("addr:street")
    if not street:
        return tags.get("addr:suburb") or tags.get("addr:city") or fallback_location

    housenumber = tags.get("addr:housenumber")
    parts = [f"{housenumber} {street}" if housenumber else street]
    city = tags.get("addr:city") or tags.get("addr:suburb")
    if city:
        parts.append(city)
    postcode = tags.get("addr:postcode")
    if postcode:
        parts.append(postcode)
    address = ", ".join(parts)
    return address[:250]


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


def fetch_osm_activities(
    latitude: float,
    longitude: float,
    radius_km: float = DEFAULT_RADIUS_KM,
    tags: dict[tuple[str, str], tuple[str, str, float, bool]] | None = None,
    result_limit: int = MAX_RESULTS_PER_DESTINATION * 3,
) -> list[dict]:
    """Fetch nearby real POIs from Overpass. Raises OsmIngestionError on any
    network/parse failure -- callers should treat this the same way the rest
    of this app treats a flaky third-party API (skip, don't crash).

    Retries once on a transient failure (429/502/503/504) after a short
    backoff -- see TRANSIENT_STATUS_CODES above for why just one.
    """
    query_data = {"data": _build_query(latitude, longitude, radius_km, tags or _OSM_TAGS, result_limit)}

    for attempt in range(2):
        try:
            # POST, not GET: Overpass's own docs recommend this for anything
            # beyond a trivial query -- a GET with this much query data in
            # the URL gets rejected outright (observed 406 Not Acceptable).
            response = httpx.post(
                OVERPASS_URL, data=query_data, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
            )
            if response.status_code in TRANSIENT_STATUS_CODES and attempt == 0:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else RETRY_BACKOFF_SECONDS
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response.json()["elements"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise OsmIngestionError(str(exc)) from exc

    raise OsmIngestionError(f"Overpass still returning {response.status_code} after one retry")


def normalize_osm_element_raw(
    element: dict, origin_lat: float, origin_lon: float, fallback_location: str
) -> dict[str, Any] | None:
    """Maps one raw Overpass element onto activity-shaped fields, relative
    to an arbitrary origin point rather than a seeded Destination. Returns
    None for elements that can't produce a presentable activity (no name,
    or no resolvable coordinate -- some way/relation results lack a
    computed "center" if Overpass couldn't derive one).
    """
    tags = element.get("tags", {})
    name = tags.get("name")
    if not name:
        return None

    group, category, default_duration, default_outdoor = next(
        (
            info
            for (key, value), info in _OSM_TAGS.items()
            if tags.get(key) == value
        ),
        ("culture", "sightseeing", 1.0, True),
    )

    # Way/relation results carry their representative point under "center"
    # (see the "out center" query directive); node results have lat/lon
    # directly on the element.
    center = element.get("center") or {}
    lat = element.get("lat", center.get("lat"))
    lon = element.get("lon", center.get("lon"))
    if lat is None or lon is None:
        return None

    distance_km = haversine_km(origin_lat, origin_lon, lat, lon)
    travel_minutes = round((distance_km / ASSUMED_LOCAL_SPEED_KMH) * 60, 1)

    opening_time, closing_time = _parse_simple_opening_hours(tags.get("opening_hours"))

    return {
        "source": "osm",
        "external_id": f"{element['type']}/{element['id']}",
        "name": name,
        "description": tags.get("description"),
        "group": group,
        "category": category,
        # OSM doesn't carry pricing -- 0/unknown, the same honest gap as
        # the deal connectors' placeholder data (see
        # deal_ingestion_pipeline.md). Free real attractions (parks,
        # viewpoints, monuments) are frequently actually free, so this
        # isn't always wrong, but it's not verified either.
        "price": 0.0,
        "duration_hours": default_duration,
        "location": _build_address(tags, fallback_location),
        "opening_time": opening_time,
        "closing_time": closing_time,
        "travel_minutes": travel_minutes,
        "distance_km": round(distance_km, 2),
        "latitude": lat,
        "longitude": lon,
        "is_outdoor": default_outdoor,
    }


def normalize_osm_element(element: dict, destination: Destination) -> dict[str, Any] | None:
    """Destination-scoped wrapper around normalize_osm_element_raw, used by
    the ingestion pipeline below. Strips the "group"/"distance_km" fields
    that only make sense for live local-adventure discovery (see
    local_activities.py) since Activity has no such columns."""
    normalized = normalize_osm_element_raw(element, destination.latitude, destination.longitude, destination.name)
    if normalized is None:
        return None
    normalized.pop("group", None)
    normalized.pop("distance_km", None)
    return normalized


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
