from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.services.discovery.types import DiscoveryResult, RankedAttraction


class DiscoveryRequestSchema(BaseModel):
    latitude: float
    longitude: float
    location_label: str
    # Structured interest tags (preferred, see discovery/interests.py); free_text
    # is a fallback classified into interests when this is omitted/empty.
    interests: list[str] | None = None
    free_text: str | None = None
    max_budget: float | None = None


class AttractionRead(BaseModel):
    name: str
    address: str | None
    latitude: float
    longitude: float
    rating: float | None
    review_count: int | None
    price_level: int | None
    categories: list[str]
    hours: dict[str, str] | None
    review_summary: str | None
    photos: list[str]
    engines: list[str]
    score: float
    score_breakdown: dict[str, float]

    @classmethod
    def from_ranked(cls, ranked: "RankedAttraction") -> "AttractionRead":
        attraction = ranked.attraction
        return cls(
            name=attraction.candidate.name,
            address=attraction.candidate.address,
            latitude=attraction.candidate.latitude,
            longitude=attraction.candidate.longitude,
            rating=attraction.rating,
            review_count=attraction.review_count,
            price_level=attraction.price_level,
            categories=attraction.categories,
            hours=attraction.hours,
            review_summary=attraction.review_summary,
            photos=attraction.photos,
            engines=sorted(attraction.candidate.engines),
            score=ranked.score,
            score_breakdown=ranked.score_breakdown,
        )


class RecommendationBucketsRead(BaseModel):
    best_overall: list[AttractionRead]
    best_value: list[AttractionRead]
    best_hidden_gem: list[AttractionRead]
    best_family: list[AttractionRead]
    best_evening: list[AttractionRead]
    best_rainy_day: list[AttractionRead]
    best_free: list[AttractionRead]


class RouteLegRead(BaseModel):
    from_name: str
    to_name: str
    distance_text: str | None
    duration_text: str | None
    duration_minutes: float | None


class DiscoveryRouteRead(BaseModel):
    legs: list[RouteLegRead]
    total_duration_minutes: float


class DiscoveryResponse(BaseModel):
    buckets: RecommendationBucketsRead
    route: DiscoveryRouteRead | None
    warnings: list[str]

    @classmethod
    def from_result(cls, result: "DiscoveryResult") -> "DiscoveryResponse":
        buckets = result.buckets
        route = result.route
        return cls(
            buckets=RecommendationBucketsRead(
                best_overall=[AttractionRead.from_ranked(r) for r in buckets.best_overall],
                best_value=[AttractionRead.from_ranked(r) for r in buckets.best_value],
                best_hidden_gem=[AttractionRead.from_ranked(r) for r in buckets.best_hidden_gem],
                best_family=[AttractionRead.from_ranked(r) for r in buckets.best_family],
                best_evening=[AttractionRead.from_ranked(r) for r in buckets.best_evening],
                best_rainy_day=[AttractionRead.from_ranked(r) for r in buckets.best_rainy_day],
                best_free=[AttractionRead.from_ranked(r) for r in buckets.best_free],
            ),
            route=DiscoveryRouteRead(
                legs=[
                    RouteLegRead(
                        from_name=leg.from_name,
                        to_name=leg.to_name,
                        distance_text=leg.distance_text,
                        duration_text=leg.duration_text,
                        duration_minutes=leg.duration_minutes,
                    )
                    for leg in route.legs
                ],
                total_duration_minutes=route.total_duration_minutes,
            )
            if route is not None
            else None,
            warnings=result.warnings,
        )
