from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_activities_source_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Which ingestion source produced this row, e.g. "osm" -- null for the
    # hand-curated seed activities. Combined with external_id, this is what
    # makes re-running OSM ingestion an upsert instead of piling up
    # duplicates; both null on seed rows never collides since SQL treats
    # NULL as distinct from NULL in a unique constraint.
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Where within the destination this activity happens -- a full street
    # address when OSM ingestion found one (e.g. "350 5th Ave, New York,
    # 10118"), otherwise a neighborhood/city label for the hand-curated
    # seed activities (e.g. "Old Town Square").
    location: Mapped[str | None] = mapped_column(String(250), nullable=True)

    # The neighborhood/suburb/district this activity sits in (e.g. "Le Marais",
    # "Wicker Park"), distinct from the full `location` address string above.
    # Populated from OSM's addr:suburb tag where available; best-effort for
    # hand-curated seed activities. Used to softly favor clustering an
    # itinerary day's stops in the same area (see itinerary.py).
    neighborhood: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Comma-separated tags, e.g. "museum,history,architecture" -- richer than
    # `category` (a single primary label) so interest matching can score
    # partial overlaps instead of requiring one exact category match. Same
    # comma-separated-Text convention as Destination.interests, for the same
    # reason (zero schema drift across SQLite/Postgres).
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    def tag_list(self) -> list[str]:
        if not self.tags:
            return []
        return [tag.strip().lower() for tag in self.tags.split(",") if tag.strip()]
