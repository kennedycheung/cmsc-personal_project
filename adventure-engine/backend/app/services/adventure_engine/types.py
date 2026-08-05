"""Shared dataclasses for the adventure recommendation engine.

See documentation/adventure_recommendation_engine.md for the full pipeline
write-up: Location Resolution -> Candidate Generation -> Nearby Attraction
Discovery -> Activity Clustering -> Scoring -> Ranking -> Recommendation
Generation -> Itinerary Generation.
"""

from dataclasses import dataclass, field

from app.services.local_activities import LocalActivity


@dataclass
class AdventureRequest:
    latitude: float
    longitude: float
    location_label: str
    radius_km: float = 15.0
    # Structured interest tags -- OSM group names (nature, food, culture,
    # entertainment, shopping, outdoor_recreation, relaxation) or finer
    # category names (museum, cafe, ...), same vocabulary local_activities.py
    # already groups discoveries by.
    interests: list[str] = field(default_factory=list)
    max_budget: float | None = None
    travel_date: str | None = None  # ISO date, optional -- enables real weather scoring


@dataclass
class AdventureCluster:
    """A group of nearby OSM-discovered activities treated as one coherent
    "adventure" -- the unit this engine scores and ranks, rather than
    scoring isolated, unrelated places one at a time."""

    activities: list[LocalActivity]
    center_lat: float
    center_lon: float
    groups: set[str]
    categories: set[str]


@dataclass
class ScoreReason:
    factor: str
    score: float  # 0-1
    weight: float
    reason: str  # human-readable, template-generated -- never fabricated/LLM text


@dataclass
class ScoredAdventure:
    cluster: AdventureCluster
    total_score: float
    confidence: float
    reasons: list[ScoreReason]
    summary: str


@dataclass
class ItinerarySlot:
    slot: str  # "morning" | "late_morning" | "lunch" | "afternoon" | "dinner" | "evening"
    activity: LocalActivity
    start_time: str
    end_time: str
    walking_minutes_from_previous: float | None


@dataclass
class AdventureItinerary:
    slots: list[ItinerarySlot]
    optional_activities: list[LocalActivity]
    total_walking_minutes: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class AdventureRecommendation:
    location_label: str
    latitude: float
    longitude: float
    total_score: float
    confidence: float
    reasons: list[ScoreReason]
    summary: str
    activities: list[LocalActivity]
    itinerary: AdventureItinerary | None
