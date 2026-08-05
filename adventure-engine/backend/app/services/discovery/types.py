"""Shared dataclasses for the Activity Discovery Engine pipeline (SerpAPI-based).

See documentation/activity_discovery_engine.md for the full pipeline write-up.
"""

from dataclasses import dataclass, field


@dataclass
class DiscoveryRequest:
    latitude: float
    longitude: float
    location_label: str
    # Structured interest tags (preferred -- same chip-based convention used
    # elsewhere in this app, e.g. AVAILABLE_INTERESTS on the frontend).
    interests: list[str] = field(default_factory=list)
    # Free-text fallback, classified into `interests` when none are given directly.
    free_text: str | None = None
    max_budget: float | None = None


@dataclass
class RawResult:
    """One hit from a single discovery-search engine, before merging."""

    engine: str  # e.g. "google_events", "yelp"
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    # e.g. {"tripadvisor": "187147", "yelp": "maman-new-york-22"} -- used to
    # drive Step 5 enrichment lookups.
    external_ids: dict[str, str] = field(default_factory=dict)
    rating: float | None = None
    review_count: int | None = None
    price_level: int | None = None  # 0 (free) .. 4 (very expensive)
    categories: list[str] = field(default_factory=list)
    is_event: bool = False
    event_date: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class CandidateAttraction:
    """One or more RawResults merged into a single real-world attraction (Step 4)."""

    name: str
    address: str | None
    latitude: float
    longitude: float
    external_ids: dict[str, str]
    engines: set[str]
    sources: list[RawResult]
    rating: float | None = None
    review_count: int | None = None
    price_level: int | None = None
    categories: list[str] = field(default_factory=list)
    has_current_event: bool = False


@dataclass
class EnrichedAttraction:
    """A CandidateAttraction after Step 5 Place/Review enrichment (if it was
    within the top-N enriched -- see enrichment.py). Fields fall back to the
    candidate's own pre-enrichment values when enrichment didn't add more."""

    candidate: CandidateAttraction
    hours: dict[str, str] | None = None
    price_level: int | None = None
    rating: float | None = None
    review_count: int | None = None
    review_summary: str | None = None
    photos: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)


@dataclass
class RankedAttraction:
    attraction: EnrichedAttraction
    score: float
    score_breakdown: dict[str, float]


@dataclass
class RecommendationBuckets:
    best_overall: list[RankedAttraction] = field(default_factory=list)
    best_value: list[RankedAttraction] = field(default_factory=list)
    best_hidden_gem: list[RankedAttraction] = field(default_factory=list)
    best_family: list[RankedAttraction] = field(default_factory=list)
    best_evening: list[RankedAttraction] = field(default_factory=list)
    best_rainy_day: list[RankedAttraction] = field(default_factory=list)
    best_free: list[RankedAttraction] = field(default_factory=list)


@dataclass
class RouteLeg:
    from_name: str
    to_name: str
    distance_text: str | None
    duration_text: str | None
    duration_minutes: float | None


@dataclass
class DiscoveryRoute:
    legs: list[RouteLeg]
    total_duration_minutes: float


@dataclass
class DiscoveryResult:
    buckets: RecommendationBuckets
    route: DiscoveryRoute | None
    warnings: list[str]
