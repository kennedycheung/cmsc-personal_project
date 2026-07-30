"""Placeholder tourism-promotion connector.

City/regional tourism boards, and deal aggregators like Groupon or Travelzoo,
don't offer a free public feed for this kind of promotion either -- most
require a business/affiliate agreement. This connector returns realistic
sample data shaped the way a real promotions feed would look, so swapping
in a live source later only means changing this function's body.
"""

SOURCE = "tourism_placeholder"


def fetch_tourism_promotions() -> list[dict]:
    return [
        {
            "promo_id": "TOUR-001",
            "headline": "Kyoto Temple & Garden Pass",
            "destination": "Kyoto, Japan",
            "bundle_price_usd": 45.0,
            "value_price_usd": 90.0,
            "tags": ["culture", "history"],
            "landing_page": "https://example-tourism.test/promos/tour-001",
            "expires_on": "2026-12-31",
        },
        {
            "promo_id": "TOUR-002",
            "headline": "Marrakech Medina Explorer Pass",
            "destination": "Marrakech, Morocco",
            "bundle_price_usd": 25.0,
            "value_price_usd": 55.0,
            "tags": ["culture", "food", "shopping"],
            "landing_page": "https://example-tourism.test/promos/tour-002",
            "expires_on": "2026-11-30",
        },
        {
            "promo_id": "TOUR-003",
            "headline": "Banff National Park Adventure Combo",
            "destination": "Banff National Park, Canada",
            "bundle_price_usd": 110.0,
            "value_price_usd": 180.0,
            "tags": ["hiking", "scenery", "wildlife"],
            "landing_page": "https://example-tourism.test/promos/tour-003",
            "expires_on": "2026-10-31",
        },
        {
            "promo_id": "TOUR-004",
            "headline": "Cape Town City Pass",
            "destination": "Cape Town, South Africa",
            "bundle_price_usd": 60.0,
            "value_price_usd": 105.0,
            "tags": ["adventure", "scenery", "food"],
            "landing_page": "https://example-tourism.test/promos/tour-004",
            "expires_on": "2027-01-31",
        },
        {
            "promo_id": "TOUR-005",
            "headline": "Barcelona Gaudí Experience Pass",
            "destination": "Barcelona, Spain",
            "bundle_price_usd": 40.0,
            "value_price_usd": 70.0,
            "tags": ["culture", "architecture"],
            "landing_page": "https://example-tourism.test/promos/tour-005",
            "expires_on": "2026-12-15",
        },
    ]
