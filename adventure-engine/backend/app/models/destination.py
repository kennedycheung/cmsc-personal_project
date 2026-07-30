from typing import TYPE_CHECKING

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.airport import Airport
    from app.models.deal import Deal


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Estimated cost of a typical day in this destination (lodging + food + local transport).
    budget_per_day: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Comma-separated interest tags, e.g. "hiking,food,nightlife". Kept as text rather
    # than a join table so SQLite and Postgres both support it with zero schema drift.
    interests: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 0 (generic/touristy) - 10 (rare/one-of-a-kind) curated rating.
    uniqueness_score: Mapped[float] = mapped_column(Float, nullable=False, default=5)

    # 0 (easy to reach and navigate) - 10 (hard to reach/navigate) curated rating.
    travel_difficulty: Mapped[float] = mapped_column(Float, nullable=False, default=5)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # ISO 4217 code of the local currency, e.g. "JPY". Used by currency
    # arbitrage (see documentation/backpacker_optimizations.md).
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Comma-separated 12 floats, Jan..Dec, relative cost multipliers (1.0 =
    # average). Curated from real tourist-season patterns; see
    # documentation/backpacker_optimizations.md (seasonal arbitrage).
    seasonal_multipliers: Mapped[str | None] = mapped_column(Text, nullable=True)

    activities: Mapped[list["Activity"]] = relationship(
        back_populates="destination", cascade="all, delete-orphan"
    )

    # No delete-orphan cascade: unlike activities, a deal isn't "owned" by its
    # destination match (destination_id is a best-effort link set by the
    # ingestion pipeline, not an intrinsic property of the deal).
    deals: Mapped[list["Deal"]] = relationship(back_populates="destination")

    airports: Mapped[list["Airport"]] = relationship(
        back_populates="destination", cascade="all, delete-orphan"
    )

    def interest_list(self) -> list[str]:
        if not self.interests:
            return []
        return [tag.strip() for tag in self.interests.split(",") if tag.strip()]

    def seasonal_multiplier_list(self) -> list[float]:
        """12 floats, Jan..Dec. Falls back to all-1.0 (no seasonal effect) if unset."""
        if not self.seasonal_multipliers:
            return [1.0] * 12
        values = [float(v.strip()) for v in self.seasonal_multipliers.split(",") if v.strip()]
        return values if len(values) == 12 else [1.0] * 12
