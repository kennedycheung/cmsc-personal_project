from pydantic import BaseModel


class LocalActivityRead(BaseModel):
    name: str
    description: str | None = None
    group: str
    category: str
    location: str
    latitude: float
    longitude: float
    distance_km: float
    duration_hours: float
    is_outdoor: bool
    opening_time: str | None = None
    closing_time: str | None = None


class LocalActivitiesResponse(BaseModel):
    origin_label: str
    radius_km: float
    groups: dict[str, list[LocalActivityRead]]
