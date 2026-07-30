from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.deal import Deal
from app.schemas.deal import DealRead, IngestionSummaryRead
from app.services.deals.pipeline import run_ingestion

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/", response_model=list[DealRead])
def list_deals(
    deal_type: str | None = Query(None, description="Filter by 'airline', 'hotel', or 'tourism'"),
    destination_id: int | None = Query(None, description="Filter to deals matched to this destination"),
    active_only: bool = Query(True, description="Exclude deals past their valid_until date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[DealRead]:
    stmt = select(Deal)
    if deal_type:
        stmt = stmt.where(Deal.deal_type == deal_type)
    if destination_id is not None:
        stmt = stmt.where(Deal.destination_id == destination_id)

    deals = list(db.execute(stmt).scalars().all())
    if active_only:
        deals = [deal for deal in deals if deal.is_active()]

    return [DealRead.from_model(deal) for deal in deals[skip : skip + limit]]


@router.get("/{deal_id}", response_model=DealRead)
def get_deal(deal_id: int, db: Session = Depends(get_db)) -> DealRead:
    deal = db.get(Deal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return DealRead.from_model(deal)


@router.post("/ingest", response_model=IngestionSummaryRead)
def trigger_ingestion(db: Session = Depends(get_db)) -> IngestionSummaryRead:
    """Re-runs every connector and upserts results into the deals table.

    Safe to call repeatedly: deals are keyed by (source, external_id), so
    re-ingestion updates existing rows instead of duplicating them.
    """
    summary = run_ingestion(db)
    return IngestionSummaryRead(
        inserted=summary.inserted,
        updated=summary.updated,
        errors=summary.errors,
        by_connector=summary.by_connector,
    )
