from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.schemas.activity import ActivityRead
from app.schemas.destination import DestinationRead

if TYPE_CHECKING:
    from app.services.itinerary import DayPlan, ItineraryResult


class ScheduledActivity(BaseModel):
    activity: ActivityRead
    start_time: str
    end_time: str


class DayWeather(BaseModel):
    date: str
    condition: str
    temperature_max: float
    temperature_min: float
    precipitation_probability: float
    # True when this is a historical-average "typical weather" estimate for
    # a date too far ahead for a real forecast, rather than an actual
    # Open-Meteo forecast.
    is_estimate: bool = False


class DayItinerary(BaseModel):
    day: int
    activities: list[ScheduledActivity]
    total_cost: float
    total_travel_minutes: float
    weather: DayWeather | None = None

    @classmethod
    def from_day_plan(cls, day_plan: "DayPlan") -> "DayItinerary":
        return cls(
            day=day_plan.day,
            activities=[
                ScheduledActivity(
                    activity=ActivityRead.model_validate(item.activity),
                    start_time=item.start_time,
                    end_time=item.end_time,
                )
                for item in day_plan.activities
            ],
            total_cost=day_plan.total_cost,
            total_travel_minutes=day_plan.total_travel_minutes,
            weather=DayWeather(
                date=day_plan.weather.date,
                condition=day_plan.weather.condition,
                temperature_max=day_plan.weather.temperature_max,
                temperature_min=day_plan.weather.temperature_min,
                precipitation_probability=day_plan.weather.precipitation_probability,
                is_estimate=day_plan.weather.is_estimate,
            )
            if day_plan.weather is not None
            else None,
        )


class RegenerateDayRequest(BaseModel):
    day: int
    days: int
    locked_activity_ids: list[int] = []
    budget: float | None = None
    interests: str | None = None
    start_date: date | None = None


class ItineraryResponse(BaseModel):
    destination: DestinationRead
    days: list[DayItinerary]
    total_cost: float
    warnings: list[str]

    @classmethod
    def from_result(cls, result: "ItineraryResult") -> "ItineraryResponse":
        return cls(
            destination=DestinationRead.from_model(result.destination),
            days=[DayItinerary.from_day_plan(day) for day in result.days],
            total_cost=result.total_cost,
            warnings=result.warnings,
        )
