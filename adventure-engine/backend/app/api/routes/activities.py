from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.activity import Activity
from app.models.destination import Destination
from app.schemas.activity import ActivityRead, OsmIngestionSummaryRead
from app.services.osm_activities import ingest_osm_activities

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/", response_model=list[ActivityRead])
def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[Activity]:
    return list(db.execute(select(Activity).offset(skip).limit(limit)).scalars().all())


@router.get("/destination/{destination_id}", response_model=list[ActivityRead])
def get_activities_for_destination(destination_id: int, db: Session = Depends(get_db)) -> list[Activity]:
    destination = db.get(Destination, destination_id)
    if destination is None:
        raise HTTPException(status_code=404, detail=f"Destination {destination_id} not found")

    stmt = select(Activity).where(Activity.destination_id == destination_id)
    return list(db.execute(stmt).scalars().all())


@router.get("/{activity_id}/alternatives", response_model=list[ActivityRead])
def get_activity_alternatives(
    activity_id: int,
    exclude_ids: str | None = Query(
        None, description="Comma-separated activity ids already used elsewhere in the trip"
    ),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[Activity]:
    """Other activities in the same destination, ranked by tag overlap with
    the target -- used by the itinerary editing UI's "swap this stop"
    action. Same set-intersection idea as recommendation.py's interest
    matching, just activity-to-activity instead of interests-to-destination.
    """
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")

    excluded_ids = {activity_id}
    if exclude_ids:
        excluded_ids.update(int(raw_id) for raw_id in exclude_ids.split(",") if raw_id.strip().isdigit())

    candidates = list(
        db.execute(
            select(Activity).where(
                Activity.destination_id == activity.destination_id,
                Activity.id.notin_(excluded_ids),
            )
        ).scalars().all()
    )

    target_tags = set(activity.tag_list())
    if activity.category:
        target_tags.add(activity.category.strip().lower())

    def _tag_overlap(candidate: Activity) -> int:
        candidate_tags = set(candidate.tag_list())
        if candidate.category:
            candidate_tags.add(candidate.category.strip().lower())
        return len(target_tags & candidate_tags)

    candidates.sort(key=_tag_overlap, reverse=True)
    return candidates[:limit]


@router.post("/ingest-osm", response_model=OsmIngestionSummaryRead)
def trigger_osm_ingestion(
    destination_id: int | None = Query(None, description="Limit ingestion to one destination; omit for all"),
    db: Session = Depends(get_db),
) -> OsmIngestionSummaryRead:
    """Pulls real nearby points of interest from OpenStreetMap's Overpass
    API and upserts them as activities -- real museums, parks, viewpoints,
    landmarks, etc. rather than only the hand-curated seed set.

    Not run automatically on startup (unlike deal ingestion): Overpass is a
    real shared public service, so this is on-demand only. Safe to call
    repeatedly -- activities are keyed by (source, external_id), so
    re-ingestion updates existing rows instead of duplicating them.
    """
    try:
        summary = ingest_osm_activities(db, destination_id=destination_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return OsmIngestionSummaryRead(
        inserted=summary.inserted,
        updated=summary.updated,
        skipped_unnamed=summary.skipped_unnamed,
        errors=summary.errors,
        by_destination=summary.by_destination,
    )
