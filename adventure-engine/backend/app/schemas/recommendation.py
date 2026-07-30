from pydantic import BaseModel

from app.schemas.destination import DestinationRead


class ScoreBreakdown(BaseModel):
    budget_fit: float
    interest_match: float
    uniqueness: float
    cost_efficiency: float
    travel_difficulty: float
    weather: float


class RecommendationRead(BaseModel):
    destination: DestinationRead
    adventure_score: float
    score_breakdown: ScoreBreakdown
    weather_summary: str | None = None
