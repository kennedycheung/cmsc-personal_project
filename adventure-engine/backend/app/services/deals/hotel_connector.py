"""Placeholder hotel-deal connector.

Hotel rate/deal data (Booking.com Partner API, Expedia Rapid API, etc.)
requires an approved commercial partnership -- there's no free public API
for this either. This connector returns realistic sample data shaped the
way a real hotel-deal API response would look, so swapping in a live
source later only means changing this function's body.
"""

SOURCE = "hotel_placeholder"


def fetch_hotel_deals() -> list[dict]:
    return [
        {
            "promo_code": "HTL-001",
            "hotel_name": "Riad Yasmine",
            "city": "Marrakech",
            "country": "Morocco",
            "star_rating": 4,
            "nightly_rate_usd": 85.0,
            "rack_rate_usd": 150.0,
            "booking_url": "https://example-hotels.test/deals/htl-001",
            "stay_window_start": "2026-08-15",
            "stay_window_end": "2027-02-28",
        },
        {
            "promo_code": "HTL-002",
            "hotel_name": "Fairmont Banff Springs",
            "city": "Banff",
            "country": "Canada",
            "star_rating": 5,
            "nightly_rate_usd": 220.0,
            "rack_rate_usd": 340.0,
            "booking_url": "https://example-hotels.test/deals/htl-002",
            "stay_window_start": "2026-09-01",
            "stay_window_end": "2026-11-15",
        },
        {
            "promo_code": "HTL-003",
            "hotel_name": "Boutique Ryokan Kiyomizu",
            "city": "Kyoto",
            "country": "Japan",
            "star_rating": 4,
            "nightly_rate_usd": 140.0,
            "rack_rate_usd": 210.0,
            "booking_url": "https://example-hotels.test/deals/htl-003",
            "stay_window_start": "2026-10-01",
            "stay_window_end": "2027-01-31",
        },
        {
            "promo_code": "HTL-004",
            "hotel_name": "Cape Grace Hotel",
            "city": "Cape Town",
            "country": "South Africa",
            "star_rating": 5,
            "nightly_rate_usd": 180.0,
            "rack_rate_usd": 310.0,
            "booking_url": "https://example-hotels.test/deals/htl-004",
            "stay_window_start": "2026-08-01",
            "stay_window_end": "2026-12-20",
        },
        {
            "promo_code": "HTL-005",
            "hotel_name": "Hotel Praktik Bakery",
            "city": "Barcelona",
            "country": "Spain",
            "star_rating": 3,
            "nightly_rate_usd": 95.0,
            "rack_rate_usd": 150.0,
            "booking_url": "https://example-hotels.test/deals/htl-005",
            "stay_window_start": "2026-09-15",
            "stay_window_end": "2027-01-10",
        },
    ]
