from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.time import utc_now_iso
from app.database.connection import get_db
from app.models.destination import Destination
from app.models.favorite_destination import FavoriteDestination
from app.models.user import User
from app.schemas.favorite import FavoriteCreate, FavoriteRead

router = APIRouter(prefix="/favorites", tags=["favorites"])


def _find_favorite(db: Session, user_id: int, destination_id: int) -> FavoriteDestination | None:
    return db.execute(
        select(FavoriteDestination).where(
            FavoriteDestination.user_id == user_id, FavoriteDestination.destination_id == destination_id
        )
    ).scalar_one_or_none()


@router.get("/", response_model=list[FavoriteRead])
def list_favorites(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[FavoriteRead]:
    stmt = select(FavoriteDestination).where(FavoriteDestination.user_id == current_user.id)
    favorites = list(db.execute(stmt).scalars().all())
    return [FavoriteRead.from_model(favorite) for favorite in favorites]


@router.post("/", response_model=FavoriteRead, status_code=201)
def add_favorite(
    payload: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoriteRead:
    destination = db.get(Destination, payload.destination_id)
    if destination is None:
        raise HTTPException(status_code=404, detail=f"Destination {payload.destination_id} not found")

    existing = _find_favorite(db, current_user.id, payload.destination_id)
    if existing is not None:
        return FavoriteRead.from_model(existing)

    favorite = FavoriteDestination(
        user_id=current_user.id, destination_id=payload.destination_id, created_at=utc_now_iso()
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return FavoriteRead.from_model(favorite)


@router.delete("/{destination_id}", status_code=204)
def remove_favorite(
    destination_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    existing = _find_favorite(db, current_user.id, destination_id)
    if existing is not None:
        db.delete(existing)
        db.commit()
