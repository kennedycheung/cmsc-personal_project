"""Placeholder airline fare-deal connector.

Real-time airline fare data (Amadeus, Skyscanner's partner feed, airline
GDS access, etc.) requires a paid/approved partnership -- there's no free
public API for this. This connector returns realistic sample data shaped
the way a real fare-deal API response would look, so the normalizer and
pipeline downstream don't need to change when a real source is wired in
later -- only this function's body would.
"""

SOURCE = "airline_placeholder"


def fetch_airline_deals() -> list[dict]:
    return [
        {
            "fare_id": "AIR-001",
            "origin_airport": "JFK",
            "destination_city": "Lisbon, Portugal",
            "airline": "TAP Air Portugal",
            "cabin": "Economy",
            "fare_usd": 412.0,
            "typical_fare_usd": 780.0,
            "deep_link": "https://example-airfare.test/deals/air-001",
            "departure_window_start": "2026-09-01",
            "departure_window_end": "2026-11-30",
        },
        {
            "fare_id": "AIR-002",
            "origin_airport": "LAX",
            "destination_city": "Kyoto, Japan",
            "airline": "ANA",
            "cabin": "Economy",
            "fare_usd": 650.0,
            "typical_fare_usd": 1100.0,
            "deep_link": "https://example-airfare.test/deals/air-002",
            "departure_window_start": "2026-10-01",
            "departure_window_end": "2027-01-15",
        },
        {
            "fare_id": "AIR-003",
            "origin_airport": "ORD",
            "destination_city": "Cape Town, South Africa",
            "airline": "United",
            "cabin": "Economy",
            "fare_usd": 890.0,
            "typical_fare_usd": 1450.0,
            "deep_link": "https://example-airfare.test/deals/air-003",
            "departure_window_start": "2026-08-15",
            "departure_window_end": "2026-12-01",
        },
        {
            "fare_id": "AIR-004",
            "origin_airport": "SFO",
            "destination_city": "Reykjavik, Iceland",
            "airline": "Icelandair",
            "cabin": "Economy",
            "fare_usd": 340.0,
            "typical_fare_usd": 560.0,
            "deep_link": "https://example-airfare.test/deals/air-004",
            "departure_window_start": "2026-09-10",
            "departure_window_end": "2027-03-01",
        },
        {
            "fare_id": "AIR-005",
            "origin_airport": "JFK",
            "destination_city": "Barcelona, Spain",
            "airline": "Iberia",
            "cabin": "Economy",
            "fare_usd": 390.0,
            "typical_fare_usd": 620.0,
            "deep_link": "https://example-airfare.test/deals/air-005",
            "departure_window_start": "2026-09-20",
            "departure_window_end": "2026-12-15",
        },
    ]
