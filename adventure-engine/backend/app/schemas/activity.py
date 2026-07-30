from pydantic import BaseModel, ConfigDict


class ActivityRead(BaseModel):
    id: int
    destination_id: int
    name: str
    description: str | None = None
    category: str | None = None
    price: float
    duration_hours: float | None = None
    location: str | None = None
    opening_time: str | None = None
    closing_time: str | None = None
    travel_minutes: float
    latitude: float
    longitude: float
    is_outdoor: bool
    # "osm" for activities pulled live from OpenStreetMap; null for the
    # hand-curated seed activities.
    source: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OsmIngestionSummaryRead(BaseModel):
    inserted: int
    updated: int
    skipped_unnamed: int
    errors: list[str]
    by_destination: dict[str, int]
