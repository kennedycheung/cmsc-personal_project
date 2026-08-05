"""Response shapes for the adventure recommendation engine.
See documentation/adventure_recommendation_engine.md for the pipeline.
"""

from pydantic import BaseModel, ConfigDict


class LocalActivityRead(BaseModel):
    name: str
    description: str | None
    group: str
    category: str
    location: str
    latitude: float
    longitude: float
    distance_km: float
    duration_hours: float
    is_outdoor: bool
    opening_time: str | None
    closing_time: str | None

    model_config = ConfigDict(from_attributes=True)


class ScoreReasonRead(BaseModel):
    factor: str
    score: float
    weight: float
    reason: str


class ItinerarySlotRead(BaseModel):
    slot: str
    activity: LocalActivityRead
    start_time: str
    end_time: str
    walking_minutes_from_previous: float | None


class AdventureItineraryRead(BaseModel):
    slots: list[ItinerarySlotRead]
    optional_activities: list[LocalActivityRead]
    total_walking_minutes: float
    warnings: list[str]


class AdventureRecommendationRead(BaseModel):
    location_label: str
    latitude: float
    longitude: float
    total_score: float
    confidence: float
    reasons: list[ScoreReasonRead]
    summary: str
    activities: list[LocalActivityRead]
    itinerary: AdventureItineraryRead | None


class AdventureRecommendationRequest(BaseModel):
    latitude: float
    longitude: float
    location_label: str
    radius_km: float = 15.0
    interests: list[str] | None = None
    max_budget: float | None = None


class AdventureRecommendationResponse(BaseModel):
    recommendations: list[AdventureRecommendationRead]
    warnings: list[str]
