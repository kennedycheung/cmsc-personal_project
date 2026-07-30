from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination
    from app.models.user import User


class FavoriteDestination(Base):
    __tablename__ = "favorite_destinations"
    __table_args__ = (UniqueConstraint("user_id", "destination_id", name="uq_favorite_user_destination"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"), nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)

    user: Mapped["User"] = relationship(back_populates="favorite_destinations")
    destination: Mapped["Destination"] = relationship()
