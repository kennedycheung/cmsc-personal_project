"""Maps each connector's raw, source-specific shape into the common set of
fields the `Deal` model expects. Each connector speaks its own "dialect"
(mirroring what a real airline/hotel/tourism API would actually return);
normalizing them here is what lets the pipeline treat all three uniformly.
"""

from typing import Any

from app.services.deals.airline_connector import SOURCE as AIRLINE_SOURCE
from app.services.deals.hotel_connector import SOURCE as HOTEL_SOURCE
from app.services.deals.tourism_connector import SOURCE as TOURISM_SOURCE


def _discount_percent(price: float, original_price: float | None) -> float | None:
    if not original_price or original_price <= 0:
        return None
    return round((1 - price / original_price) * 100, 1)


def normalize_airline_deal(raw: dict[str, Any]) -> dict[str, Any]:
    price = raw["fare_usd"]
    original_price = raw.get("typical_fare_usd")
    return {
        "deal_type": "airline",
        "source": AIRLINE_SOURCE,
        "external_id": raw["fare_id"],
        "title": f"{raw['origin_airport']} → {raw['destination_city']} on {raw['airline']}",
        "description": f"{raw['cabin']} fare deal on {raw['airline']}.",
        "location": raw["destination_city"],
        "price": price,
        "original_price": original_price,
        "discount_percent": _discount_percent(price, original_price),
        "currency": "USD",
        "url": raw.get("deep_link"),
        "valid_from": raw.get("departure_window_start"),
        "valid_until": raw.get("departure_window_end"),
        "categories": "flights",
    }


def normalize_hotel_deal(raw: dict[str, Any]) -> dict[str, Any]:
    price = raw["nightly_rate_usd"]
    original_price = raw.get("rack_rate_usd")
    return {
        "deal_type": "hotel",
        "source": HOTEL_SOURCE,
        "external_id": raw["promo_code"],
        "title": f"{raw['hotel_name']} ({raw.get('star_rating', '?')}★)",
        "description": f"Discounted nightly rate at {raw['hotel_name']}.",
        "location": f"{raw['city']}, {raw['country']}",
        "price": price,
        "original_price": original_price,
        "discount_percent": _discount_percent(price, original_price),
        "currency": "USD",
        "url": raw.get("booking_url"),
        "valid_from": raw.get("stay_window_start"),
        "valid_until": raw.get("stay_window_end"),
        "categories": "lodging",
    }


def normalize_tourism_deal(raw: dict[str, Any]) -> dict[str, Any]:
    price = raw["bundle_price_usd"]
    original_price = raw.get("value_price_usd")
    return {
        "deal_type": "tourism",
        "source": TOURISM_SOURCE,
        "external_id": raw["promo_id"],
        "title": raw["headline"],
        "description": f"Bundled tourism promotion: {raw['headline']}.",
        "location": raw["destination"],
        "price": price,
        "original_price": original_price,
        "discount_percent": _discount_percent(price, original_price),
        "currency": "USD",
        "url": raw.get("landing_page"),
        "valid_from": None,
        "valid_until": raw.get("expires_on"),
        "categories": ",".join(raw.get("tags", [])),
    }
