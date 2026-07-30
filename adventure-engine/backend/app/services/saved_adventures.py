"""Generates the itinerary snapshot stored on a SavedAdventure. Reuses the
same generate_itinerary() the /api/itineraries endpoint calls, so "save this
adventure" and "preview this itinerary" always agree with each other.
"""

from sqlalchemy.orm import Session

from app.schemas.itinerary import ItineraryResponse
from app.services.itinerary import generate_itinerary


def generate_itinerary_snapshot(
    db: Session,
    destination_id: int,
    days: int,
    budget: float | None,
    interests: str | None,
) -> str:
    """Raises DestinationNotFoundError (from generate_itinerary) if the
    destination doesn't exist -- callers should let that propagate to a 404."""
    result = generate_itinerary(db, destination_id=destination_id, days=days, budget=budget, interests=interests)
    return ItineraryResponse.from_result(result).model_dump_json()
