from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_deals_source_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    # Nullable: a deal isn't always cleanly attributable to one of our seeded
    # destinations (e.g. a flight deal to a city we don't have data for yet).
    destination_id: Mapped[int | None] = mapped_column(ForeignKey("destinations.id"), nullable=True, index=True)

    # "airline" | "hotel" | "tourism". Plain string rather than a native ENUM
    # so SQLite and Postgres both support it with zero schema drift.
    deal_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Which connector produced this row, e.g. "airline_placeholder". Combined
    # with external_id below, this is what makes re-running ingestion an
    # upsert instead of piling up duplicate rows every run.
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(String(150), nullable=False)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    original_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # "YYYY-MM-DD"; same short-string convention as Activity.opening_time.
    valid_from: Mapped[str | None] = mapped_column(String(10), nullable=True)
    valid_until: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Comma-separated tags, e.g. "flights" or "culture,history" -- same
    # convention as Destination.interests.
    categories: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)

    destination: Mapped["Destination | None"] = relationship(back_populates="deals")

    def category_list(self) -> list[str]:
        if not self.categories:
            return []
        return [tag.strip() for tag in self.categories.split(",") if tag.strip()]

    def is_active(self) -> bool:
        if not self.valid_until:
            return True
        try:
            return date.fromisoformat(self.valid_until) >= date.today()
        except ValueError:
            return True
