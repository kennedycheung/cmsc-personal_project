from pydantic import BaseModel, ConfigDict

from app.models.deal import Deal


class DealRead(BaseModel):
    id: int
    destination_id: int | None
    deal_type: str
    source: str
    title: str
    description: str | None = None
    location: str
    price: float
    original_price: float | None = None
    discount_percent: float | None = None
    currency: str
    url: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    categories: list[str] = []
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, deal: Deal) -> "DealRead":
        return cls(
            id=deal.id,
            destination_id=deal.destination_id,
            deal_type=deal.deal_type,
            source=deal.source,
            title=deal.title,
            description=deal.description,
            location=deal.location,
            price=deal.price,
            original_price=deal.original_price,
            discount_percent=deal.discount_percent,
            currency=deal.currency,
            url=deal.url,
            valid_from=deal.valid_from,
            valid_until=deal.valid_until,
            categories=deal.category_list(),
            created_at=deal.created_at,
            updated_at=deal.updated_at,
        )


class IngestionSummaryRead(BaseModel):
    inserted: int
    updated: int
    errors: list[str]
    by_connector: dict[str, int]
