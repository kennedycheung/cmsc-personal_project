"""Clean provider interfaces for future paid/keyed integrations this engine
doesn't have credentials for yet -- FlightProvider, HotelProvider,
TransitProvider, EventProvider, RestaurantProvider. Every concrete class
here raises ProviderUnavailableError; none fabricate data. The point is
that `engine.py` can reference `providers.get("events")` today, and wiring
in a real Ticketmaster/Amadeus/etc. integration later is swapping one
registry entry, not changing the engine's orchestration.

Deliberately NOT placeholder'd here, because a real implementation already
exists elsewhere in this app and is reused directly instead:
- Weather: `services/weather.py` (Open-Meteo, real, free) -- scoring.py
  calls `is_bad_weather`/`is_good_weather` directly.
- Basic restaurant/cafe discovery: OSM via `local_activities.py`'s "food"
  group -- already real data, not a placeholder. `RestaurantProvider`
  below is specifically for a *premium* data source (ratings, reviews,
  reservations) beyond bare existence/location, which OSM doesn't carry.
- A SerpAPI-based multi-source aggregator (Google/TripAdvisor/Yelp,
  including a Google Events source) already exists as a separate, optional
  feature -- see `services/discovery/` and
  documentation/activity_discovery_engine.md. It's intentionally not wired
  into this engine's core scoring (this engine works with zero paid keys);
  `EventProvider` below represents a *dedicated* ticketed-events API
  (Ticketmaster/Eventbrite) as a distinct future path, not a duplicate of
  the discovery engine's Google Events source.
"""

from typing import Protocol


class ProviderUnavailableError(Exception):
    """Raised by every provider below -- there is no real implementation
    yet. Callers must treat this exactly like any other graceful-
    degradation case in this app (see WeatherUnavailableError): skip or
    score neutrally, never crash the whole request."""


class FlightProvider(Protocol):
    def search_flights(self, origin: str, destination: str, date: str) -> list[dict]: ...


class HotelProvider(Protocol):
    def search_hotels(self, latitude: float, longitude: float, check_in: str, check_out: str) -> list[dict]: ...


class TransitProvider(Protocol):
    def get_routes(self, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> list[dict]: ...


class EventProvider(Protocol):
    def search_events(self, latitude: float, longitude: float, date: str) -> list[dict]: ...


class RestaurantProvider(Protocol):
    """A *premium* restaurant data source (ratings, reviews, reservation
    availability) -- distinct from OSM's basic restaurant/cafe discovery,
    which already works today via local_activities.py."""

    def search_restaurants(self, latitude: float, longitude: float) -> list[dict]: ...


class _NotConfiguredFlightProvider:
    def search_flights(self, origin: str, destination: str, date: str) -> list[dict]:
        raise ProviderUnavailableError(
            "No FlightProvider configured -- flight search needs a keyed fare API (e.g. a GDS or "
            "Skyscanner/Kiwi-style aggregator), not currently available."
        )


class _NotConfiguredHotelProvider:
    def search_hotels(self, latitude: float, longitude: float, check_in: str, check_out: str) -> list[dict]:
        raise ProviderUnavailableError(
            "No HotelProvider configured -- lodging search needs a keyed API (e.g. Booking.com/Expedia "
            "affiliate API), not currently available."
        )


class _NotConfiguredTransitProvider:
    def get_routes(self, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> list[dict]:
        raise ProviderUnavailableError(
            "No TransitProvider configured -- real-time public transit routing needs a keyed API "
            "(e.g. Google Directions transit mode, a regional GTFS-realtime feed), not currently available."
        )


class _NotConfiguredEventProvider:
    def search_events(self, latitude: float, longitude: float, date: str) -> list[dict]:
        raise ProviderUnavailableError(
            "No EventProvider configured -- ticketed event listings need a keyed API "
            "(Ticketmaster Discovery API or Eventbrite), not currently available."
        )


class _NotConfiguredRestaurantProvider:
    def search_restaurants(self, latitude: float, longitude: float) -> list[dict]:
        raise ProviderUnavailableError(
            "No RestaurantProvider configured -- premium restaurant data (ratings/reviews/reservations) "
            "needs a keyed API (e.g. Yelp Fusion); basic restaurant discovery already works via OSM."
        )


# Swap any entry here for a real implementation once credentials exist --
# engine.py never needs to change, only this registry.
PROVIDERS: dict[str, object] = {
    "flights": _NotConfiguredFlightProvider(),
    "hotels": _NotConfiguredHotelProvider(),
    "transit": _NotConfiguredTransitProvider(),
    "events": _NotConfiguredEventProvider(),
    "restaurants": _NotConfiguredRestaurantProvider(),
}
