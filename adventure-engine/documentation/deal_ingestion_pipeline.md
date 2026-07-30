# Deal Ingestion Pipeline

Implemented in [`backend/app/services/deals/`](../backend/app/services/deals/)
and exposed via `GET /api/deals`, `GET /api/deals/{id}`, and `POST /api/deals/ingest`.

## Overview

Three connectors — airline, hotel, tourism — each fetch raw deal records in
their own source-specific shape, a normalizer maps each shape into the
common set of `Deal` model fields, and the pipeline best-effort matches each
deal to a seeded destination and upserts it into the `deals` table. The
whole thing also runs once automatically on backend startup (after seeding),
in addition to being triggerable on demand via `POST /api/deals/ingest`.

## Why placeholder connectors

Real-time airline fares, hotel rates, and tourism promotions are all
commercial data. Amadeus, Skyscanner's partner feed, Booking.com's Partner
API, Expedia Rapid API — every realistic option requires a paid or approved
business relationship; none of them offer a free public endpoint the way
Open-Meteo or OSRM do elsewhere in this app. So each connector is a
placeholder: a pure function returning realistic sample data shaped exactly
the way a real API response would look. Swapping in a live source later is
scoped to rewriting one connector's function body — the normalizer, pipeline,
model, and API surface don't need to change.

## Connectors

Each lives in its own module under `backend/app/services/deals/` and returns
`list[dict]` in a distinct, realistic raw shape:

| Connector | Function | Raw shape mimics |
|---|---|---|
| Airline | `airline_connector.fetch_airline_deals()` | A fare-deal API (`fare_id`, `origin_airport`, `destination_city`, `fare_usd`, `typical_fare_usd`, `departure_window_*`) |
| Hotel | `hotel_connector.fetch_hotel_deals()` | A hotel-rate API (`promo_code`, `hotel_name`, `city`/`country`, `nightly_rate_usd`, `rack_rate_usd`, `stay_window_*`) |
| Tourism | `tourism_connector.fetch_tourism_promotions()` | A city/tourism-board promo feed (`promo_id`, `headline`, `destination`, `bundle_price_usd`, `value_price_usd`, `tags`, `expires_on`) |

Each ships 5 sample records — 4 whose location matches a seeded destination
(Lisbon, Kyoto, Cape Town, Reykjavik/Banff/Marrakech depending on connector)
and 1 that deliberately doesn't (Barcelona, which isn't in the seed set),
so both the matched and unmatched paths are exercised out of the box.

## Normalization

`normalizer.py` has one `normalize_*_deal(raw) -> dict` function per
connector, each mapping its source's raw fields onto the common `Deal`
columns (`deal_type`, `source`, `external_id`, `title`, `description`,
`location`, `price`, `original_price`, `discount_percent`, `currency`,
`url`, `valid_from`, `valid_until`, `categories`). `discount_percent` is
computed as `(1 - price / original_price) * 100` when an original/list
price is present, rather than trusting each source to report it.

## Destination matching

`_match_destination` in `pipeline.py` is intentionally simple: case-insensitive
substring match of a seeded destination's `name` against the deal's
`location` string, falling back to `country` if no name matches. No
destination match is not an error — most real-world deals won't cleanly
map onto one of the ~64 seeded destinations, and `destination_id` is
nullable specifically to allow that.

## Upsert / idempotency

Deals are keyed by `(source, external_id)` (a unique constraint on the
table). Re-running ingestion updates existing rows — including re-checking
the destination match — instead of inserting duplicates. This is what makes
it safe to run automatically on every backend startup as well as on demand
via `POST /api/deals/ingest`.

## Failure isolation

Each connector's fetch and each record's normalization is wrapped
independently: a broken connector or one malformed record is recorded in
`IngestionSummary.errors` and skipped, not allowed to abort the whole
pipeline run. The response from `POST /api/deals/ingest` reports
`inserted`, `updated`, `errors`, and a per-connector processed count.

## Note on history

This was a fresh implementation, not a fix-up of what predated it. A
`scrapers/` scaffold (`deal.py`, `groupon.py`, `travelzoo.py`,
`promotions.py`, now removed) had a `Deal` dataclass and two hardcoded
fixture sources with a similar shape (price, discount, expiry) — a
reasonable conceptual sketch, but it lived at the repo root, wasn't backed
by a database (deals were held in an in-process list that reset on
restart), and was never imported by the backend. Separately,
`backend/app/services/ingest.py`, `normalizer.py`, and `ingestion_sources/`
(also removed) were an earlier, broken pipeline for a different resource
entirely ("attractions," not deals) that was never wired up to anything.
