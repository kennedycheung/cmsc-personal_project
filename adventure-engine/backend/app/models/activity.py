from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Where within the destination this activity happens, e.g. "Old Town Square".
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # "HH:MM" 24-hour local time. Both null means the activity has no fixed hours
    # (treated as open all day by the itinerary scheduler).
    opening_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    closing_time: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # Approximate travel time (minutes) to reach this activity from a central point
    # or the previous stop. A simplification standing in for real geo-routing.
    travel_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=15)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # True if bad weather (rain/storm) meaningfully hurts this activity (a hike, a
    # scenic gondola) as opposed to something weather-resistant (a museum, a warm
    # indoor tasting room, an open-air hot spring). Drives itinerary weather scoring.
    is_outdoor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    destination: Mapped["Destination"] = relationship(back_populates="activities")
