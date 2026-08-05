from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.itinerary import DayItinerary, ItineraryResponse, RegenerateDayRequest
from app.services.itinerary import DestinationNotFoundError, generate_itinerary, regenerate_day

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.get("/{destination_id}", response_model=ItineraryResponse)
def get_itinerary(
    destination_id: int,
    days: int = Query(3, ge=1, le=14, description="Number of days to plan"),
    budget: float | None = Query(None, ge=0, description="Total trip budget across all days"),
    interests: str | None = Query(None, description="Comma-separated interests, e.g. 'hiking,food'"),
    start_date: date | None = Query(
        None,
        description=(
            "First day of the trip (YYYY-MM-DD). Within 16 days, uses a real weather "
            "forecast; farther out, uses a historical-average 'typical weather' estimate "
            "for that time of year instead. Omit to schedule starting today."
        ),
    ),
    db: Session = Depends(get_db),
) -> ItineraryResponse:
    try:
        result = generate_itinerary(
            db, destination_id=destination_id, days=days, budget=budget, interests=interests, start_date=start_date
        )
    except DestinationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Destination {destination_id} not found")

    return ItineraryResponse.from_result(result)


@router.post("/{destination_id}/regenerate-day", response_model=DayItinerary)
def regenerate_itinerary_day(
    destination_id: int,
    body: RegenerateDayRequest,
    db: Session = Depends(get_db),
) -> DayItinerary:
    """Rebuilds a single day of an itinerary the user is editing client-side
    -- `locked_activity_ids` should be every activity already used on the
    trip's *other* days, so the rebuilt day doesn't duplicate them."""
    try:
        day_plan = regenerate_day(
            db,
            destination_id=destination_id,
            day=body.day,
            days=body.days,
            locked_activity_ids=set(body.locked_activity_ids),
            budget=body.budget,
            interests=body.interests,
            start_date=body.start_date,
        )
    except DestinationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Destination {destination_id} not found")

    return DayItinerary.from_day_plan(day_plan)
