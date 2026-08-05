"""Builds a named-time-slot itinerary for one chosen AdventureCluster:
morning / late_morning / lunch / afternoon / dinner / evening, plus
optional activities that didn't fit, walking time between consecutive
stops, and fixed buffer time -- a richer time model than a flat activity
list.

Real point-to-point walking time isn't computed here (that would mean an
OSRM call per candidate cluster during scoring/ranking, not just the one
the user ends up seeing) -- this uses the same documented-assumption
walking speed as scoring.py's walkability factor. The frontend's existing
OSRM integration (useWalkingRoute) already computes a real route for the
final chosen itinerary the same way for stored-Activity itineraries; the
same approach applies here once this reaches a UI.

Slot start times are fixed rather than dynamically shifted by how long the
previous stop ran -- a documented simplification for this first version,
same spirit as itinerary.py's fixed DAY_START.
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from app.services.adventure_engine.types import AdventureCluster, AdventureItinerary, ItinerarySlot
from app.services.local_activities import LocalActivity
from app.services.optimizations.geo import haversine_km

WALKING_SPEED_KMH = 4.8
BUFFER_MINUTES = 10
DEFAULT_DURATION_HOURS = 1.0

SLOT_ORDER = ["morning", "late_morning", "lunch", "afternoon", "dinner", "evening"]
SLOT_START_TIMES: dict[str, time] = {
    "morning": time(9, 0),
    "late_morning": time(10, 30),
    "lunch": time(12, 30),
    "afternoon": time(14, 30),
    "dinner": time(18, 30),
    "evening": time(20, 30),
}

# Which groups/categories fit which named slot -- a documented assumption
# table, same spirit as itinerary.py's _MORNING_TAGS/_EVENING_TAGS but
# mapped onto local_activities.py's OSM group/category vocabulary.
SLOT_HINTS: dict[str, set[str]] = {
    "morning": {"cafe", "bakery", "viewpoint", "hiking", "botanical_garden", "park", "wildlife_refuge"},
    "late_morning": {"museum", "gallery", "historic_site", "landmark", "library"},
    "lunch": {"restaurant", "food_hall", "cafe", "market"},
    "afternoon": {"museum", "gallery", "landmark", "market", "mall", "bookstore", "spa"},
    "dinner": {"restaurant", "brewery", "winery", "food_hall"},
    "evening": {"theater", "cinema", "nightlife", "arcade"},
}


def _tags_for(activity: LocalActivity) -> set[str]:
    return {activity.group.lower(), activity.category.lower()}


def _best_for_slot(slot: str, remaining: list[LocalActivity]) -> LocalActivity | None:
    """Only returns a match when one of `remaining` actually fits this
    slot's hints -- a slot with nothing suitable left is skipped entirely
    rather than force-filled with an arbitrary leftover (e.g. a theater
    landing in the "lunch" slot just because it happened to still be in the
    pool). Anything that never matches any slot ends up in
    AdventureItinerary.optional_activities instead, which is exactly what
    that field is for."""
    hints = SLOT_HINTS.get(slot, set())
    matching = [a for a in remaining if _tags_for(a) & hints]
    return matching[0] if matching else None


@dataclass
class _ItineraryBuildState:
    remaining: list[LocalActivity]
    previous: LocalActivity | None = None
    total_walking_minutes: float = 0.0


def build_itinerary(cluster: AdventureCluster) -> AdventureItinerary:
    state = _ItineraryBuildState(remaining=list(cluster.activities))
    slots: list[ItinerarySlot] = []

    for slot_name in SLOT_ORDER:
        if not state.remaining:
            break
        activity = _best_for_slot(slot_name, state.remaining)
        if activity is None:
            continue
        state.remaining.remove(activity)

        start = SLOT_START_TIMES[slot_name]
        duration_hours = activity.duration_hours or DEFAULT_DURATION_HOURS
        end = (datetime.combine(datetime.min, start) + timedelta(hours=duration_hours)).time()

        walking_minutes = None
        if state.previous is not None:
            distance_km = haversine_km(
                state.previous.latitude, state.previous.longitude, activity.latitude, activity.longitude
            )
            walking_minutes = round((distance_km / WALKING_SPEED_KMH) * 60 + BUFFER_MINUTES, 1)
            state.total_walking_minutes += walking_minutes

        slots.append(
            ItinerarySlot(
                slot=slot_name,
                activity=activity,
                start_time=start.strftime("%H:%M"),
                end_time=end.strftime("%H:%M"),
                walking_minutes_from_previous=walking_minutes,
            )
        )
        state.previous = activity

    warnings = [] if slots else ["No activities could be scheduled into named time slots."]

    return AdventureItinerary(
        slots=slots,
        optional_activities=state.remaining,
        total_walking_minutes=round(state.total_walking_minutes, 1),
        warnings=warnings,
    )
