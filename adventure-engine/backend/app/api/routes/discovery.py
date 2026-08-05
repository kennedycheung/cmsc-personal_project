from fastapi import APIRouter, HTTPException

from app.schemas.discovery import DiscoveryRequestSchema, DiscoveryResponse
from app.services.discovery.engine import discover
from app.services.discovery.serpapi_client import SerpApiNotConfiguredError
from app.services.discovery.types import DiscoveryRequest

router = APIRouter(prefix="/discover", tags=["discovery"])


@router.post("/", response_model=DiscoveryResponse)
def discover_activities(body: DiscoveryRequestSchema) -> DiscoveryResponse:
    """Runs the Activity Discovery Engine (SerpAPI-based, see
    documentation/activity_discovery_engine.md) and returns the 7 named
    recommendation buckets plus a chained route through "Best Overall".
    """
    request = DiscoveryRequest(
        latitude=body.latitude,
        longitude=body.longitude,
        location_label=body.location_label,
        interests=body.interests or [],
        free_text=body.free_text,
        max_budget=body.max_budget,
    )
    try:
        result = discover(request)
    except SerpApiNotConfiguredError:
        raise HTTPException(status_code=503, detail="SerpAPI is not configured (SERPAPI_KEY missing).")

    return DiscoveryResponse.from_result(result)
