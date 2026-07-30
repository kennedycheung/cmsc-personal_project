import json

from pydantic import BaseModel, ConfigDict, Field

from app.models.saved_adventure import SavedAdventure


class SavedAdventureCreate(BaseModel):
    destination_id: int
    name: str = Field(min_length=1, max_length=200)
    days: int = Field(default=3, ge=1, le=14)
    budget: float | None = Field(default=None, ge=0)
    interests: list[str] | None = None


class SavedAdventureRead(BaseModel):
    id: int
    destination_id: int
    name: str
    days: int
    budget: float | None = None
    interests: list[str] = []
    itinerary: dict
    created_at: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, saved: SavedAdventure) -> "SavedAdventureRead":
        return cls(
            id=saved.id,
            destination_id=saved.destination_id,
            name=saved.name,
            days=saved.days,
            budget=saved.budget,
            interests=saved.interest_list(),
            itinerary=json.loads(saved.itinerary_snapshot),
            created_at=saved.created_at,
        )
