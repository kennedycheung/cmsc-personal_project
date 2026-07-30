from fastapi import APIRouter, HTTPException, Query

from app.schemas.local_activity import LocalActivitiesResponse, LocalActivityRead
from app.services.local_activities import (
    ACTIVITY_GROUPS,
    DEFAULT_RADIUS_KM,
    LocalActivityDiscoveryError,
    discover_local_activities,
)

router = APIRouter(prefix="/local-activities", tags=["local-activities"])


@router.get("/", response_model=LocalActivitiesResponse)
def list_local_activities(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    origin_label: str = Query("your area", description="Human-readable label for the origin point"),
    radius_km: float = Query(DEFAULT_RADIUS_KM, gt=0, le=50),
    groups: str | None = Query(
        None,
        description=f"Comma-separated subset of: {', '.join(ACTIVITY_GROUPS)}. Omit for all.",
    ),
) -> LocalActivitiesResponse:
    requested_groups = [g.strip() for g in groups.split(",") if g.strip()] if groups else None

    try:
        grouped = discover_local_activities(
            latitude, longitude, origin_label, radius_km=radius_km, groups=requested_groups
        )
    except LocalActivityDiscoveryError as exc:
        raise HTTPException(status_code=502, detail=f"Couldn't reach OpenStreetMap: {exc}")

    return LocalActivitiesResponse(
        origin_label=origin_label,
        radius_km=radius_km,
        groups={
            group: [
                LocalActivityRead(
                    name=a.name,
                    description=a.description,
                    group=a.group,
                    category=a.category,
                    location=a.location,
                    latitude=a.latitude,
                    longitude=a.longitude,
                    distance_km=a.distance_km,
                    duration_hours=a.duration_hours,
                    is_outdoor=a.is_outdoor,
                    opening_time=a.opening_time,
                    closing_time=a.closing_time,
                )
                for a in activities
            ]
            for group, activities in grouped.items()
        },
    )
