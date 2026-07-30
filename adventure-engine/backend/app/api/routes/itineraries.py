from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.itinerary import ItineraryResponse
from app.services.itinerary import DestinationNotFoundError, generate_itinerary

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.get("/{destination_id}", response_model=ItineraryResponse)
def get_itinerary(
    destination_id: int,
    days: int = Query(3, ge=1, le=14, description="Number of days to plan"),
    budget: float | None = Query(None, ge=0, description="Total trip budget across all days"),
    interests: str | None = Query(None, description="Comma-separated interests, e.g. 'hiking,food'"),
    db: Session = Depends(get_db),
) -> ItineraryResponse:
    try:
        result = generate_itinerary(db, destination_id=destination_id, days=days, budget=budget, interests=interests)
    except DestinationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Destination {destination_id} not found")

    return ItineraryResponse.from_result(result)
