from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.schemas.activity import ActivityRead
from app.schemas.destination import DestinationRead

if TYPE_CHECKING:
    from app.services.itinerary import ItineraryResult


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


class DayItinerary(BaseModel):
    day: int
    activities: list[ScheduledActivity]
    total_cost: float
    total_travel_minutes: float
    weather: DayWeather | None = None


class ItineraryResponse(BaseModel):
    destination: DestinationRead
    days: list[DayItinerary]
    total_cost: float
    warnings: list[str]

    @classmethod
    def from_result(cls, result: "ItineraryResult") -> "ItineraryResponse":
        return cls(
            destination=DestinationRead.from_model(result.destination),
            days=[
                DayItinerary(
                    day=day.day,
                    activities=[
                        ScheduledActivity(
                            activity=ActivityRead.model_validate(item.activity),
                            start_time=item.start_time,
                            end_time=item.end_time,
                        )
                        for item in day.activities
                    ],
                    total_cost=day.total_cost,
                    total_travel_minutes=day.total_travel_minutes,
                    weather=DayWeather(
                        date=day.weather.date,
                        condition=day.weather.condition,
                        temperature_max=day.weather.temperature_max,
                        temperature_min=day.weather.temperature_min,
                        precipitation_probability=day.weather.precipitation_probability,
                    )
                    if day.weather is not None
                    else None,
                )
                for day in result.days
            ],
            total_cost=result.total_cost,
            warnings=result.warnings,
        )
