from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)

    max_budget_per_day: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Comma-separated, same convention as Destination.interests.
    interests: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Free-text rather than a fixed enum -- matches the frontend's
    # TripPreferenceForm options ("Budget", "Luxury", "Family", "Solo",
    # "Couples") without hard-coding that list into the backend.
    travel_style: Mapped[str | None] = mapped_column(String(50), nullable=True)

    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)

    user: Mapped["User"] = relationship(back_populates="preferences")

    def interest_list(self) -> list[str]:
        if not self.interests:
            return []
        return [tag.strip() for tag in self.interests.split(",") if tag.strip()]
