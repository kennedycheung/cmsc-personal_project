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
