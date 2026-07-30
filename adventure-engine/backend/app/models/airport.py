from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class Airport(Base):
    """A candidate airport for reaching a destination. Most destinations have
    none modeled (their obvious primary airport is genuinely the only
    reasonable choice) -- see documentation/backpacker_optimizations.md for
    why only a few destinations carry real alternate-airport data.
    """

    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"), nullable=False, index=True)

    iata_code: Mapped[str] = mapped_column(String(3), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)

    ground_transport_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    ground_transport_minutes: Mapped[float] = mapped_column(Float, nullable=False)

    # Curated placeholder -- no live multi-airport fare API exists any more
    # than a live single-fare one does (see deal_ingestion_pipeline.md).
    baseline_fare_usd: Mapped[float] = mapped_column(Float, nullable=False)

    # The "obvious" choice a traveler would pick without this optimization.
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    destination: Mapped["Destination"] = relationship(back_populates="airports")
