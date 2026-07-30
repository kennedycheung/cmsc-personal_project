from pydantic import BaseModel, ConfigDict


class ActivityRead(BaseModel):
    id: int
    destination_id: int
    name: str
    description: str | None = None
    category: str | None = None
    price: float
    duration_hours: float | None = None
    location: str | None = None
    opening_time: str | None = None
    closing_time: str | None = None
    travel_minutes: float
    latitude: float
    longitude: float
    is_outdoor: bool

    model_config = ConfigDict(from_attributes=True)
