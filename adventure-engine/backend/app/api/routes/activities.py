from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.activity import Activity
from app.models.destination import Destination
from app.schemas.activity import ActivityRead

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
