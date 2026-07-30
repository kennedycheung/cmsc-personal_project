from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.time import utc_now_iso
from app.database.connection import get_db
from app.models.saved_adventure import SavedAdventure
from app.models.user import User
from app.schemas.saved_adventure import SavedAdventureCreate, SavedAdventureRead
from app.services.itinerary import DestinationNotFoundError
from app.services.saved_adventures import generate_itinerary_snapshot

router = APIRouter(prefix="/saved-adventures", tags=["saved-adventures"])


@router.get("/", response_model=list[SavedAdventureRead])
def list_saved_adventures(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[SavedAdventureRead]:
    stmt = select(SavedAdventure).where(SavedAdventure.user_id == current_user.id)
    saved = list(db.execute(stmt).scalars().all())
    return [SavedAdventureRead.from_model(item) for item in saved]


@router.post("/", response_model=SavedAdventureRead, status_code=201)
def create_saved_adventure(
    payload: SavedAdventureCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedAdventureRead:
    interests_str = ",".join(payload.interests) if payload.interests else None

    try:
        snapshot = generate_itinerary_snapshot(
            db,
            destination_id=payload.destination_id,
            days=payload.days,
            budget=payload.budget,
            interests=interests_str,
        )
    except DestinationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Destination {payload.destination_id} not found")

    saved = SavedAdventure(
        user_id=current_user.id,
        destination_id=payload.destination_id,
        name=payload.name,
        days=payload.days,
        budget=payload.budget,
        interests=interests_str,
        itinerary_snapshot=snapshot,
        created_at=utc_now_iso(),
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return SavedAdventureRead.from_model(saved)


@router.get("/{saved_id}", response_model=SavedAdventureRead)
def get_saved_adventure(
    saved_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> SavedAdventureRead:
    saved = db.get(SavedAdventure, saved_id)
    if saved is None or saved.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"Saved adventure {saved_id} not found")
    return SavedAdventureRead.from_model(saved)


@router.delete("/{saved_id}", status_code=204)
def delete_saved_adventure(
    saved_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    saved = db.get(SavedAdventure, saved_id)
    if saved is None or saved.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"Saved adventure {saved_id} not found")
    db.delete(saved)
    db.commit()
