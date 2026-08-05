from .activities import router as activities_router
from .adventures import router as adventures_router
from .auth import router as auth_router
from .deals import router as deals_router
from .destinations import router as destinations_router
from .discovery import router as discovery_router
from .favorites import router as favorites_router
from .geocode import router as geocode_router
from .health import router as health_router
from .itineraries import router as itineraries_router
from .local_activities import router as local_activities_router
from .optimizations import router as optimizations_router
from .preferences import router as preferences_router
from .recommendations import router as recommendations_router
from .saved_adventures import router as saved_adventures_router

__all__ = [
    "health_router",
    "destinations_router",
    "activities_router",
    "adventures_router",
    "recommendations_router",
    "itineraries_router",
    "deals_router",
    "auth_router",
    "preferences_router",
    "saved_adventures_router",
    "favorites_router",
    "optimizations_router",
    "geocode_router",
    "local_activities_router",
    "discovery_router",
]
