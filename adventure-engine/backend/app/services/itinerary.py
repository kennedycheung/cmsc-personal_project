"""Day-by-day itinerary generation from stored activities for a single destination.

See documentation/itinerary_algorithm.md for the full write-up of the scheduling
approach and the reasoning behind the default weights and day window.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.destination import Destination
from app.services.weather import (
    DayForecast,
    WeatherUnavailableError,
    get_forecast,
    get_weather_for_dates,
    is_bad_weather,
    is_good_weather,
)

DAY_START = time(9, 0)
DAY_END = time(21, 0)
# Activities whose tags associate them exclusively with the late-night slot
# (nightlife, breweries, ...) may run past DAY_END up to this cutoff instead
# -- a category-conditional extension of the day window, not a global one.
LATE_NIGHT_END = time(23, 59)
MAX_ACTIVITIES_PER_DAY = 4
DEFAULT_DURATION_HOURS = 1.0

SCORE_WEIGHTS: dict[str, float] = {
    "interest_match": 0.30,
    "cost_fit": 0.20,
    "travel_efficiency": 0.10,
    "weather_fit": 0.20,
    "time_fit": 0.20,
}

# How strongly repeat categories (today, or earlier in the trip) get nudged
# down so an itinerary doesn't stack e.g. four museums in a row when nothing
# else scores as highly -- multiplicative per repeat, never a hard block, so
# a sparse destination can still reuse a category if nothing else fits.
DIVERSITY_PENALTY = 0.85

# Small score bonus for an activity in a neighborhood already visited today,
# to softly favor clustering a day's stops and reduce backtracking. Additive
# and small on purpose: it should only tip close calls, not override the
# primary score-based selection.
NEIGHBORHOOD_BONUS = 0.05

# Tags/categories with a genuine real-world time-of-day association.
# Anything not listed is treated as flexible (fits any slot without penalty)
# rather than guessing an association that doesn't exist -- a documented
# assumption table, same spirit as _OSM_TAGS/_CATEGORY_SYNONYMS.
_MORNING_TAGS = {"cafe", "bakery", "hiking", "viewpoint", "botanical_garden", "national_park", "wildlife_refuge", "beach"}
_EVENING_TAGS = {"restaurant", "winery", "theater", "cinema", "sightseeing"}
_LATE_NIGHT_TAGS = {"nightlife", "brewery", "bar", "arcade", "escape_room"}


class DestinationNotFoundError(Exception):
    pass


@dataclass
class ScheduledActivityResult:
    activity: Activity
    start_time: str
    end_time: str


@dataclass
class DayPlan:
    day: int
    activities: list[ScheduledActivityResult] = field(default_factory=list)
    total_cost: float = 0.0
    total_travel_minutes: float = 0.0
    weather: DayForecast | None = None


@dataclass
class ItineraryResult:
    destination: Destination
    days: list[DayPlan]
    total_cost: float
    warnings: list[str]


def _parse_time(value: str | None, fallback: time) -> time:
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return fallback


def _add_minutes(moment: time, minutes: float) -> time:
    combined = datetime.combine(datetime.min, moment) + timedelta(minutes=minutes)
    return combined.time()


def _score_weather_fit(activity: Activity, day_forecast: DayForecast | None) -> float:
    if day_forecast is None:
        return 0.5

    if is_bad_weather(day_forecast):
        return 0.15 if activity.is_outdoor else 1.0
    if is_good_weather(day_forecast):
        return 1.0 if activity.is_outdoor else 0.6
    return 0.55 if activity.is_outdoor else 0.65


def _activity_tags(activity: Activity) -> set[str]:
    category = (activity.category or "").strip().lower()
    tags = set(activity.tag_list())
    if category:
        tags.add(category)
    return tags


def _time_slot_for(moment: time) -> str:
    if moment < time(12, 0):
        return "morning"
    if moment < time(17, 0):
        return "afternoon"
    if moment < DAY_END:
        return "evening"
    return "late_night"


def _score_time_fit(activity_tags: set[str], current_slot: str) -> float:
    preferred: set[str] = set()
    if activity_tags & _MORNING_TAGS:
        preferred.add("morning")
    if activity_tags & _EVENING_TAGS:
        preferred.add("evening")
    if activity_tags & _LATE_NIGHT_TAGS:
        preferred.add("late_night")
    if not preferred:
        return 0.6
    return 1.0 if current_slot in preferred else 0.3


def _day_cutoff_for(activity_tags: set[str]) -> time:
    is_late_night_only = bool(activity_tags & _LATE_NIGHT_TAGS) and not (
        activity_tags & _MORNING_TAGS or activity_tags & _EVENING_TAGS
    )
    return LATE_NIGHT_END if is_late_night_only else DAY_END


def _score_activity(
    activity: Activity,
    requested_interests: set[str],
    day_budget: float | None,
    max_travel_minutes: float,
    day_forecast: DayForecast | None,
    current_slot: str,
    categories_today: Counter,
    categories_trip: Counter,
    neighborhoods_today: set[str],
) -> float:
    activity_tags = _activity_tags(activity)
    if requested_interests:
        matches = requested_interests & activity_tags
        interest_match = min(1.0, len(matches) / len(requested_interests))
    else:
        interest_match = 0.5

    if day_budget is None:
        cost_fit = 1.0 if activity.price == 0 else 0.5
    elif day_budget <= 0:
        cost_fit = 1.0 if activity.price == 0 else 0.0
    else:
        cost_fit = max(0.0, min(1.0, 1.0 - activity.price / day_budget))

    travel_efficiency = 1.0 - (activity.travel_minutes / max_travel_minutes) if max_travel_minutes > 0 else 1.0
    weather_fit = _score_weather_fit(activity, day_forecast)
    time_fit = _score_time_fit(activity_tags, current_slot)

    score = (
        SCORE_WEIGHTS["interest_match"] * interest_match
        + SCORE_WEIGHTS["cost_fit"] * cost_fit
        + SCORE_WEIGHTS["travel_efficiency"] * travel_efficiency
        + SCORE_WEIGHTS["weather_fit"] * weather_fit
        + SCORE_WEIGHTS["time_fit"] * time_fit
    )

    category = (activity.category or "").strip().lower()
    repeat_count = categories_today[category] + categories_trip[category]
    if category and repeat_count:
        score *= DIVERSITY_PENALTY**repeat_count

    if activity.neighborhood and activity.neighborhood in neighborhoods_today:
        score += NEIGHBORHOOD_BONUS

    return score


def _resolve_forecast(
    destination: Destination, days: int, start_date: date | None
) -> tuple[list[DayForecast | None], list[str]]:
    warnings: list[str] = []

    if start_date is not None:
        # A known travel date: use a real forecast for days within the next
        # 16 days, and a historical-average "typical weather" estimate for
        # anything farther out (see weather.get_weather_for_dates).
        trip_dates = [start_date + timedelta(days=i) for i in range(days)]
        by_date = get_weather_for_dates(destination.latitude, destination.longitude, trip_dates)
        forecast = [by_date.get(d.isoformat()) for d in trip_dates]
        if any(day is None for day in forecast):
            warnings.append("Weather unavailable for one or more days; scheduling did not account for weather then.")
        if any(day is not None and day.is_estimate for day in forecast):
            warnings.append(
                "Some days are far enough ahead that weather is a historical-average estimate, not a real forecast."
            )
        return forecast, warnings

    try:
        return get_forecast(destination.latitude, destination.longitude, days), warnings
    except WeatherUnavailableError:
        warnings.append("Weather forecast unavailable; scheduling did not account for weather.")
        return [], warnings


def _build_day(
    pool: list[Activity],
    requested_interests: set[str],
    day_budget: float | None,
    max_travel_minutes: float,
    day_forecast: DayForecast | None,
    categories_trip: Counter,
) -> tuple[list[ScheduledActivityResult], list[Activity]]:
    """Builds one day's schedule by repeatedly picking the best-fitting
    remaining candidate from `pool`, re-scored after each pick since the
    best fit depends on the current time slot and on what categories/
    neighborhoods have already been picked today -- both change as the day
    is built, so a single upfront sort (the original approach) can't
    account for them.

    Returns the scheduled stops and the activities used, so the caller can
    remove them from a shared multi-day pool (generate_itinerary) or just
    discard the list for a standalone single-day rebuild (regenerate_day).
    Mutates `categories_trip` in place so multi-day callers can thread trip-
    wide diversity tracking across days; a fresh Counter can be passed for a
    single-day-only call.
    """
    current_time = DAY_START
    remaining_budget = day_budget if day_budget is not None else float("inf")
    scheduled: list[ScheduledActivityResult] = []
    used_activities: list[Activity] = []
    used_indices: list[int] = []
    categories_today: Counter = Counter()
    neighborhoods_today: set[str] = set()

    while len(scheduled) < MAX_ACTIVITIES_PER_DAY:
        current_slot = _time_slot_for(current_time)
        best_idx: int | None = None
        best_score = -1.0
        best_window: tuple[time, time] | None = None

        for idx, activity in enumerate(pool):
            if idx in used_indices:
                continue
            if activity.price > remaining_budget:
                continue

            activity_tags = _activity_tags(activity)
            opening = _parse_time(activity.opening_time, DAY_START)
            closing = _parse_time(activity.closing_time, DAY_END)
            start = max(current_time, opening)
            duration_hours = activity.duration_hours or DEFAULT_DURATION_HOURS
            end = _add_minutes(start, duration_hours * 60)

            if end > closing or end > _day_cutoff_for(activity_tags):
                continue

            score = _score_activity(
                activity,
                requested_interests,
                day_budget,
                max_travel_minutes,
                day_forecast,
                current_slot,
                categories_today,
                categories_trip,
                neighborhoods_today,
            )
            if score > best_score:
                best_score = score
                best_idx = idx
                best_window = (start, end)

        if best_idx is None:
            break

        activity = pool[best_idx]
        start, end = best_window
        scheduled.append(
            ScheduledActivityResult(
                activity=activity,
                start_time=start.strftime("%H:%M"),
                end_time=end.strftime("%H:%M"),
            )
        )
        used_indices.append(best_idx)
        used_activities.append(activity)
        remaining_budget -= activity.price
        current_time = _add_minutes(end, activity.travel_minutes)

        category = (activity.category or "").strip().lower()
        if category:
            categories_today[category] += 1
            categories_trip[category] += 1
        if activity.neighborhood:
            neighborhoods_today.add(activity.neighborhood)

    return scheduled, used_activities


def generate_itinerary(
    db: Session,
    destination_id: int,
    days: int,
    budget: float | None = None,
    interests: str | None = None,
    start_date: date | None = None,
) -> ItineraryResult:
    destination = db.get(Destination, destination_id)
    if destination is None:
        raise DestinationNotFoundError(destination_id)

    activities = list(
        db.execute(select(Activity).where(Activity.destination_id == destination_id)).scalars().all()
    )

    requested_interests = (
        {tag.strip().lower() for tag in interests.split(",") if tag.strip()} if interests else set()
    )
    day_budget = (budget / days) if budget is not None and days > 0 else None
    max_travel_minutes = max((a.travel_minutes for a in activities), default=0.0)

    warnings: list[str] = []
    if not activities:
        warnings.append(f"No stored activities exist yet for destination {destination_id}.")

    forecast, forecast_warnings = _resolve_forecast(destination, days, start_date)
    warnings.extend(forecast_warnings)

    # Remaining candidates for the whole trip; each activity can be used once.
    pool = list(activities)
    categories_trip: Counter = Counter()

    day_plans: list[DayPlan] = []
    for day_index in range(1, days + 1):
        day_forecast = forecast[day_index - 1] if day_index - 1 < len(forecast) else None

        scheduled, used_activities = _build_day(
            pool, requested_interests, day_budget, max_travel_minutes, day_forecast, categories_trip
        )
        for activity in used_activities:
            pool.remove(activity)

        if not scheduled and activities:
            warnings.append(
                f"Day {day_index}: no remaining stored activities fit the budget, hours, or day window."
            )

        day_plans.append(
            DayPlan(
                day=day_index,
                activities=scheduled,
                total_cost=sum(item.activity.price for item in scheduled),
                total_travel_minutes=sum(item.activity.travel_minutes for item in scheduled),
                weather=day_forecast,
            )
        )

    return ItineraryResult(
        destination=destination,
        days=day_plans,
        total_cost=sum(day.total_cost for day in day_plans),
        warnings=warnings,
    )


def regenerate_day(
    db: Session,
    destination_id: int,
    day: int,
    days: int,
    locked_activity_ids: set[int],
    budget: float | None = None,
    interests: str | None = None,
    start_date: date | None = None,
) -> DayPlan:
    """Rebuilds a single day of an itinerary, e.g. after the user edited
    other days -- `locked_activity_ids` are activities already scheduled
    elsewhere in the trip, excluded from this day's candidate pool and fed
    in as this day's starting diversity signal so it doesn't just duplicate
    what those days already picked."""
    destination = db.get(Destination, destination_id)
    if destination is None:
        raise DestinationNotFoundError(destination_id)

    activities = list(
        db.execute(select(Activity).where(Activity.destination_id == destination_id)).scalars().all()
    )
    pool = [activity for activity in activities if activity.id not in locked_activity_ids]

    requested_interests = (
        {tag.strip().lower() for tag in interests.split(",") if tag.strip()} if interests else set()
    )
    day_budget = (budget / days) if budget is not None and days > 0 else None
    max_travel_minutes = max((a.travel_minutes for a in activities), default=0.0)

    categories_trip: Counter = Counter(
        (activity.category or "").strip().lower()
        for activity in activities
        if activity.id in locked_activity_ids and activity.category
    )

    forecast, _warnings = _resolve_forecast(destination, days, start_date)
    day_forecast = forecast[day - 1] if 0 <= day - 1 < len(forecast) else None

    scheduled, _used = _build_day(pool, requested_interests, day_budget, max_travel_minutes, day_forecast, categories_trip)

    return DayPlan(
        day=day,
        activities=scheduled,
        total_cost=sum(item.activity.price for item in scheduled),
        total_travel_minutes=sum(item.activity.travel_minutes for item in scheduled),
        weather=day_forecast,
    )
