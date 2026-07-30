from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.destination import Destination
from app.schemas.destination import DestinationRead

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("/", response_model=list[DestinationRead])
def list_destinations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[DestinationRead]:
    destinations = db.execute(select(Destination).offset(skip).limit(limit)).scalars().all()
    return [DestinationRead.from_model(d) for d in destinations]


@router.get("/search", response_model=list[DestinationRead])
def search_destinations(
    region: str | None = Query(None, description="Case-insensitive, partial match on region"),
    min_budget: float | None = Query(None, ge=0, description="Minimum budget per day"),
    max_budget: float | None = Query(None, ge=0, description="Maximum budget per day"),
    interests: str | None = Query(None, description="Comma-separated interests, e.g. 'hiking,food'"),
    db: Session = Depends(get_db),
) -> list[DestinationRead]:
    if min_budget is not None and max_budget is not None and min_budget > max_budget:
        raise HTTPException(status_code=400, detail="min_budget cannot exceed max_budget")

    stmt = select(Destination)
    if region:
        stmt = stmt.where(Destination.region.ilike(f"%{region}%"))
    if min_budget is not None:
        stmt = stmt.where(Destination.budget_per_day >= min_budget)
    if max_budget is not None:
        stmt = stmt.where(Destination.budget_per_day <= max_budget)

    destinations = list(db.execute(stmt).scalars().all())

    if interests:
        requested = {tag.strip().lower() for tag in interests.split(",") if tag.strip()}
        if requested:
            destinations = [
                d for d in destinations if requested & {tag.lower() for tag in d.interest_list()}
            ]

    return [DestinationRead.from_model(d) for d in destinations]


@router.get("/{destination_id}", response_model=DestinationRead)
def get_destination(destination_id: int, db: Session = Depends(get_db)) -> DestinationRead:
    destination = db.get(Destination, destination_id)
    if destination is None:
        raise HTTPException(status_code=404, detail=f"Destination {destination_id} not found")
    return DestinationRead.from_model(destination)
