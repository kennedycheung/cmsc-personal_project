"""Day-by-day itinerary generation from stored activities for a single destination.

See documentation/itinerary_algorithm.md for the full write-up of the scheduling
approach and the reasoning behind the default weights and day window.
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.destination import Destination
from app.services.weather import DayForecast, WeatherUnavailableError, get_forecast, is_bad_weather, is_good_weather

DAY_START = time(9, 0)
DAY_END = time(21, 0)
MAX_ACTIVITIES_PER_DAY = 4
DEFAULT_DURATION_HOURS = 1.0

SCORE_WEIGHTS: dict[str, float] = {
    "interest_match": 0.4,
    "cost_fit": 0.25,
    "travel_efficiency": 0.15,
    "weather_fit": 0.20,
}


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


def _score_activity(
    activity: Activity,
    requested_interests: set[str],
    day_budget: float | None,
    max_travel_minutes: float,
    day_forecast: DayForecast | None,
) -> float:
    category = (activity.category or "").strip().lower()
    if requested_interests:
        interest_match = 1.0 if category in requested_interests else 0.3
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

    return (
        SCORE_WEIGHTS["interest_match"] * interest_match
        + SCORE_WEIGHTS["cost_fit"] * cost_fit
        + SCORE_WEIGHTS["travel_efficiency"] * travel_efficiency
        + SCORE_WEIGHTS["weather_fit"] * weather_fit
    )


def generate_itinerary(
    db: Session,
    destination_id: int,
    days: int,
    budget: float | None = None,
    interests: str | None = None,
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

    try:
        forecast = get_forecast(destination.latitude, destination.longitude, days)
    except WeatherUnavailableError:
        forecast = []
        warnings.append("Weather forecast unavailable; scheduling did not account for weather.")

    # Remaining candidates for the whole trip; each activity can be used once.
    pool = list(activities)

    day_plans: list[DayPlan] = []
    for day_index in range(1, days + 1):
        day_forecast = forecast[day_index - 1] if day_index - 1 < len(forecast) else None

        # Weather changes day to day, so the ranking is recomputed fresh for
        # each day rather than sorted once for the whole trip up front.
        pool.sort(
            key=lambda a: _score_activity(a, requested_interests, day_budget, max_travel_minutes, day_forecast),
            reverse=True,
        )

        current_time = DAY_START
        remaining_budget = day_budget if day_budget is not None else float("inf")
        scheduled: list[ScheduledActivityResult] = []
        used: list[int] = []

        for idx, activity in enumerate(pool):
            if len(scheduled) >= MAX_ACTIVITIES_PER_DAY:
                break
            if activity.price > remaining_budget:
                continue

            opening = _parse_time(activity.opening_time, DAY_START)
            closing = _parse_time(activity.closing_time, DAY_END)
            start = max(current_time, opening)
            duration_hours = activity.duration_hours or DEFAULT_DURATION_HOURS
            end = _add_minutes(start, duration_hours * 60)

            if end > closing or end > DAY_END:
                continue

            scheduled.append(
                ScheduledActivityResult(
                    activity=activity,
                    start_time=start.strftime("%H:%M"),
                    end_time=end.strftime("%H:%M"),
                )
            )
            used.append(idx)
            remaining_budget -= activity.price
            current_time = _add_minutes(end, activity.travel_minutes)

        for idx in sorted(used, reverse=True):
            pool.pop(idx)

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
