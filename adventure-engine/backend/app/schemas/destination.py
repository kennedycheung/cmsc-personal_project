from pydantic import BaseModel, ConfigDict

from app.models.destination import Destination


class DestinationRead(BaseModel):
    id: int
    name: str
    country: str
    region: str
    description: str | None = None
    budget_per_day: float
    interests: list[str] = []
    uniqueness_score: float
    travel_difficulty: float
    latitude: float
    longitude: float
    currency: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, destination: Destination) -> "DestinationRead":
        return cls(
            id=destination.id,
            name=destination.name,
            country=destination.country,
            region=destination.region,
            description=destination.description,
            budget_per_day=destination.budget_per_day,
            interests=destination.interest_list(),
            uniqueness_score=destination.uniqueness_score,
            travel_difficulty=destination.travel_difficulty,
            latitude=destination.latitude,
            longitude=destination.longitude,
            currency=destination.currency,
        )
