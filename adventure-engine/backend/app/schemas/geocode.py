from pydantic import BaseModel


class GeocodeResultRead(BaseModel):
    latitude: float
    longitude: float
    label: str
    country: str | None = None
