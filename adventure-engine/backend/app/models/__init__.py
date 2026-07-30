from app.models.activity import Activity
from app.models.airport import Airport
from app.models.base import Base
from app.models.deal import Deal
from app.models.destination import Destination
from app.models.favorite_destination import FavoriteDestination
from app.models.saved_adventure import SavedAdventure
from app.models.user import User
from app.models.user_preference import UserPreference

__all__ = [
    "Base",
    "Destination",
    "Activity",
    "Deal",
    "User",
    "UserPreference",
    "SavedAdventure",
    "FavoriteDestination",
    "Airport",
]
