from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.favorite_destination import FavoriteDestination
    from app.models.saved_adventure import SavedAdventure
    from app.models.user_preference import UserPreference


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)

    preferences: Mapped["UserPreference | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    saved_adventures: Mapped[list["SavedAdventure"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorite_destinations: Mapped[list["FavoriteDestination"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
