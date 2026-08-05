from fastapi import APIRouter

from app.schemas.adventure_engine import (
    AdventureItineraryRead,
    AdventureRecommendationRead,
    AdventureRecommendationRequest,
    AdventureRecommendationResponse,
    ItinerarySlotRead,
    LocalActivityRead,
    ScoreReasonRead,
)
from app.services.adventure_engine.engine import recommend_adventures
from app.services.adventure_engine.types import AdventureItinerary, AdventureRequest
from app.services.local_activities import LocalActivity

router = APIRouter(prefix="/adventures", tags=["adventures"])


def _to_activity_read(activity: LocalActivity) -> LocalActivityRead:
    return LocalActivityRead.model_validate(activity)


def _to_itinerary_read(itinerary: AdventureItinerary | None) -> AdventureItineraryRead | None:
    if itinerary is None:
        return None
    return AdventureItineraryRead(
        slots=[
            ItinerarySlotRead(
                slot=s.slot,
                activity=_to_activity_read(s.activity),
                start_time=s.start_time,
                end_time=s.end_time,
                walking_minutes_from_previous=s.walking_minutes_from_previous,
            )
            for s in itinerary.slots
        ],
        optional_activities=[_to_activity_read(a) for a in itinerary.optional_activities],
        total_walking_minutes=itinerary.total_walking_minutes,
        warnings=itinerary.warnings,
    )


@router.post("/recommend", response_model=AdventureRecommendationResponse)
def recommend(body: AdventureRecommendationRequest) -> AdventureRecommendationResponse:
    """Runs the OSM-only adventure recommendation engine: discovers nearby
    real activities, clusters them into coherent adventures, scores each
    with independent factors (distance, density, diversity, walkability,
    interest match, weather, confidence), and returns ranked
    recommendations with reasoning plus a suggested itinerary for
    multi-stop clusters. Needs no paid/keyed API -- OSM/Nominatim/Overpass
    and this app's existing free weather integration only.
    """
    request = AdventureRequest(
        latitude=body.latitude,
        longitude=body.longitude,
        location_label=body.location_label,
        radius_km=body.radius_km,
        interests=body.interests or [],
        max_budget=body.max_budget,
    )
    recommendations, warnings = recommend_adventures(request)

    return AdventureRecommendationResponse(
        recommendations=[
            AdventureRecommendationRead(
                location_label=r.location_label,
                latitude=r.latitude,
                longitude=r.longitude,
                total_score=r.total_score,
                confidence=r.confidence,
                reasons=[
                    ScoreReasonRead(factor=x.factor, score=x.score, weight=x.weight, reason=x.reason)
                    for x in r.reasons
                ],
                summary=r.summary,
                activities=[_to_activity_read(a) for a in r.activities],
                itinerary=_to_itinerary_read(r.itinerary),
            )
            for r in recommendations
        ],
        warnings=warnings,
    )
