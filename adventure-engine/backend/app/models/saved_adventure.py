from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination
    from app.models.user import User


class SavedAdventure(Base):
    __tablename__ = "saved_adventures"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Comma-separated, same convention as Destination.interests.
    interests: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Serialized ItineraryResponse JSON, captured at save time. Itinerary
    # generation depends on live weather, so re-running it later could
    # produce a different plan -- this snapshot is what "saved adventure"
    # actually means: the plan as it was when the user saved it.
    itinerary_snapshot: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[str] = mapped_column(String(40), nullable=False)

    user: Mapped["User"] = relationship(back_populates="saved_adventures")
    destination: Mapped["Destination"] = relationship()

    def interest_list(self) -> list[str]:
        if not self.interests:
            return []
        return [tag.strip() for tag in self.interests.split(",") if tag.strip()]
