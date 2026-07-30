from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.time import utc_now_iso
from app.database.connection import get_db
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.preference import UserPreferenceRead, UserPreferenceUpdate

router = APIRouter(prefix="/preferences", tags=["preferences"])


def _get_or_create(db: Session, user: User) -> UserPreference:
    preference = db.execute(
        select(UserPreference).where(UserPreference.user_id == user.id)
    ).scalar_one_or_none()
    if preference is None:
        preference = UserPreference(user_id=user.id, updated_at=utc_now_iso())
        db.add(preference)
        db.commit()
        db.refresh(preference)
    return preference


@router.get("/me", response_model=UserPreferenceRead)
def get_my_preferences(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserPreferenceRead:
    return UserPreferenceRead.from_model(_get_or_create(db, current_user))


@router.put("/me", response_model=UserPreferenceRead)
def update_my_preferences(
    payload: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPreferenceRead:
    preference = _get_or_create(db, current_user)

    if payload.max_budget_per_day is not None:
        preference.max_budget_per_day = payload.max_budget_per_day
    if payload.interests is not None:
        preference.interests = ",".join(payload.interests)
    if payload.travel_style is not None:
        preference.travel_style = payload.travel_style
    preference.updated_at = utc_now_iso()

    db.commit()
    db.refresh(preference)
    return UserPreferenceRead.from_model(preference)
