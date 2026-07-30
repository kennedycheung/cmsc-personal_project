"""Orchestrates the deal ingestion pipeline: fetch from each connector,
normalize into common `Deal` fields, best-effort match to a seeded
destination, and upsert into the database.

See documentation/deal_ingestion_pipeline.md for the full write-up.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now_iso
from app.models.deal import Deal
from app.models.destination import Destination
from app.services.deals.airline_connector import fetch_airline_deals
from app.services.deals.hotel_connector import fetch_hotel_deals
from app.services.deals.normalizer import normalize_airline_deal, normalize_hotel_deal, normalize_tourism_deal
from app.services.deals.tourism_connector import fetch_tourism_promotions

# (connector name, fetch function, normalize function)
CONNECTORS: list[tuple[str, Callable[[], list[dict]], Callable[[dict], dict[str, Any]]]] = [
    ("airline", fetch_airline_deals, normalize_airline_deal),
    ("hotel", fetch_hotel_deals, normalize_hotel_deal),
    ("tourism", fetch_tourism_promotions, normalize_tourism_deal),
]


@dataclass
class IngestionSummary:
    inserted: int = 0
    updated: int = 0
    errors: list[str] = field(default_factory=list)
    by_connector: dict[str, int] = field(default_factory=dict)


def _match_destination(destinations: list[Destination], location: str) -> int | None:
    """Best-effort link to a seeded destination by name, falling back to
    country. Returns None (not an error) if nothing matches -- most deals
    won't cleanly map to one of our ~14 seeded destinations, and that's fine."""
    if not location:
        return None
    normalized_location = location.lower()

    for destination in destinations:
        if destination.name.lower() in normalized_location:
            return destination.id

    for destination in destinations:
        if destination.country.lower() in normalized_location:
            return destination.id

    return None


def run_ingestion(db: Session) -> IngestionSummary:
    summary = IngestionSummary()
    destinations = list(db.execute(select(Destination)).scalars().all())

    for connector_name, fetch_fn, normalize_fn in CONNECTORS:
        processed = 0
        try:
            raw_deals = fetch_fn()
        except Exception as exc:  # placeholder connectors won't raise, but a real one might
            summary.errors.append(f"{connector_name}: fetch failed ({exc})")
            summary.by_connector[connector_name] = 0
            continue

        for raw in raw_deals:
            try:
                normalized = normalize_fn(raw)
            except (KeyError, TypeError, ValueError) as exc:
                summary.errors.append(f"{connector_name}: could not normalize a record ({exc})")
                continue

            destination_id = _match_destination(destinations, normalized["location"])

            existing = db.execute(
                select(Deal).where(
                    Deal.source == normalized["source"], Deal.external_id == normalized["external_id"]
                )
            ).scalar_one_or_none()

            if existing is not None:
                for field_name, value in normalized.items():
                    setattr(existing, field_name, value)
                existing.destination_id = destination_id
                existing.updated_at = utc_now_iso()
                summary.updated += 1
            else:
                now = utc_now_iso()
                db.add(Deal(**normalized, destination_id=destination_id, created_at=now, updated_at=now))
                summary.inserted += 1

            processed += 1

        summary.by_connector[connector_name] = processed

    db.commit()
    return summary
