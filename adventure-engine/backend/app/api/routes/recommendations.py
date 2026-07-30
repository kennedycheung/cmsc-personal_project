from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.destination import DestinationRead
from app.schemas.recommendation import RecommendationRead, ScoreBreakdown
from app.services.recommendation import get_top_recommendations
from app.services.travel_time import TimeBucket, TravelScope, resolve_max_distance_km

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/", response_model=list[RecommendationRead])
def list_recommendations(
    max_budget: float | None = Query(None, ge=0, description="Maximum budget per day"),
    interests: str | None = Query(None, description="Comma-separated interests, e.g. 'hiking,food'"),
    top_n: int = Query(10, ge=1, le=50, description="Number of ranked destinations to return"),
    origin_lat: float | None = Query(None, ge=-90, le=90, description="Starting-location latitude"),
    origin_lon: float | None = Query(None, ge=-180, le=180, description="Starting-location longitude"),
    max_distance_km: float | None = Query(
        None, ge=0, description="Exclude destinations farther than this from the origin. "
        "Overrides time_bucket/travel_scope if both are given."
    ),
    time_bucket: TimeBucket | None = Query(
        None, description="How much time is available -- resolved into a distance constraint server-side"
    ),
    travel_scope: TravelScope | None = Query(
        None, description="stay_local/day_trip/overnight_trip/anywhere_within_budget -- refines time_bucket's distance"
    ),
    db: Session = Depends(get_db),
) -> list[RecommendationRead]:
    effective_max_distance_km = max_distance_km
    if effective_max_distance_km is None and time_bucket is not None:
        effective_max_distance_km = resolve_max_distance_km(time_bucket, travel_scope)

    ranked = get_top_recommendations(
        db,
        max_budget=max_budget,
        interests=interests,
        top_n=top_n,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        max_distance_km=effective_max_distance_km,
    )
    return [
        RecommendationRead(
            destination=DestinationRead.from_model(destination),
            adventure_score=adventure_score,
            score_breakdown=ScoreBreakdown(**breakdown),
            weather_summary=weather_summary,
        )
        for destination, adventure_score, breakdown, weather_summary in ranked
    ]
