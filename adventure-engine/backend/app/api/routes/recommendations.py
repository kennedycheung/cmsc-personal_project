from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.destination import DestinationRead
from app.schemas.recommendation import RecommendationRead, ScoreBreakdown
from app.services.recommendation import get_top_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/", response_model=list[RecommendationRead])
def list_recommendations(
    max_budget: float | None = Query(None, ge=0, description="Maximum budget per day"),
    interests: str | None = Query(None, description="Comma-separated interests, e.g. 'hiking,food'"),
    top_n: int = Query(10, ge=1, le=50, description="Number of ranked destinations to return"),
    db: Session = Depends(get_db),
) -> list[RecommendationRead]:
    ranked = get_top_recommendations(db, max_budget=max_budget, interests=interests, top_n=top_n)
    return [
        RecommendationRead(
            destination=DestinationRead.from_model(destination),
            adventure_score=adventure_score,
            score_breakdown=ScoreBreakdown(**breakdown),
            weather_summary=weather_summary,
        )
        for destination, adventure_score, breakdown, weather_summary in ranked
    ]
