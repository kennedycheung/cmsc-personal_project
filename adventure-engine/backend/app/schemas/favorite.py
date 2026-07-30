from pydantic import BaseModel, ConfigDict

from app.models.favorite_destination import FavoriteDestination
from app.schemas.destination import DestinationRead


class FavoriteCreate(BaseModel):
    destination_id: int


class FavoriteRead(BaseModel):
    id: int
    destination: DestinationRead
    created_at: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, favorite: FavoriteDestination) -> "FavoriteRead":
        return cls(
            id=favorite.id,
            destination=DestinationRead.from_model(favorite.destination),
            created_at=favorite.created_at,
        )
