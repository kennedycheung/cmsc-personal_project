from app.schemas.activity import ActivityRead
from app.schemas.airport import AirportRead
from app.schemas.auth import TokenResponse, UserLogin, UserRegister
from app.schemas.deal import DealRead, IngestionSummaryRead
from app.schemas.destination import DestinationRead
from app.schemas.favorite import FavoriteCreate, FavoriteRead
from app.schemas.itinerary import DayItinerary, ItineraryResponse, ScheduledActivity
from app.schemas.optimizations import (
    AirportOptimizationRead,
    AirportOptionRead,
    CurrencyArbitrageRead,
    MonthCostRead,
    OpenJawRead,
    OvernightTransportRead,
    PositioningRead,
    SeasonalArbitrageRead,
)
from app.schemas.preference import UserPreferenceRead, UserPreferenceUpdate
from app.schemas.recommendation import RecommendationRead
from app.schemas.saved_adventure import SavedAdventureCreate, SavedAdventureRead
from app.schemas.user import UserRead

__all__ = [
    "DestinationRead",
    "ActivityRead",
    "RecommendationRead",
    "ItineraryResponse",
    "DayItinerary",
    "ScheduledActivity",
    "DealRead",
    "IngestionSummaryRead",
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "UserRead",
    "UserPreferenceRead",
    "UserPreferenceUpdate",
    "SavedAdventureCreate",
    "SavedAdventureRead",
    "FavoriteCreate",
    "FavoriteRead",
    "AirportRead",
    "AirportOptimizationRead",
    "AirportOptionRead",
    "OvernightTransportRead",
    "OpenJawRead",
    "PositioningRead",
    "MonthCostRead",
    "SeasonalArbitrageRead",
    "CurrencyArbitrageRead",
]
