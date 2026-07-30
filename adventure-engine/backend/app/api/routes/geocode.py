from fastapi import APIRouter, HTTPException, Query

from app.schemas.geocode import GeocodeResultRead
from app.services.geocoding import GeocodeError, geocode

router = APIRouter(prefix="/geocode", tags=["geocode"])


@router.get("/", response_model=GeocodeResultRead)
def resolve_location(
    query: str = Query(..., min_length=1, description="A city or airport name, e.g. 'Chicago' or 'JFK airport'"),
) -> GeocodeResultRead:
    try:
        result = geocode(query)
    except GeocodeError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return GeocodeResultRead(
        latitude=result.latitude,
        longitude=result.longitude,
        label=result.label,
        country=result.country,
    )
