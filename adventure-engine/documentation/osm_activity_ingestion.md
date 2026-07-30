# OSM Activity Ingestion

Implemented in [`backend/app/services/osm_activities.py`](../backend/app/services/osm_activities.py)
and exposed via `POST /api/activities/ingest-osm`.

## Overview

The seeded activities in `seed.py` are hand-curated -- real, but a fixed,
finite list. This pipeline supplements that with real points of interest
pulled live from OpenStreetMap's Overpass API (free, no API key, no
signup), so a destination's activity pool isn't limited to whatever was
manually typed in ahead of time. Results are upserted into the same
`activities` table the itinerary generator already reads from -- nothing
about `itinerary.py` needed to change.

## Why Overpass, and why on-demand only

Overpass is the same kind of free, keyless, real API this project already
prefers (Open-Meteo, OSRM, Frankfurter) over anything requiring a signup.
Unlike those, though, it's explicitly a shared community resource with a
published fair-use policy -- not something built to absorb a query per
seeded destination on every backend restart. So unlike the deal pipeline
(pure local functions, safe to auto-run on every startup), OSM ingestion
is **on-demand only**, triggered by calling `POST /api/activities/ingest-osm`
yourself.

## Query

For a destination's coordinates, one Overpass query asks (in a single
request) for nearby OSM elements matching any of ~40 tags across seven
groups -- nature (beaches, lakes, viewpoints, campsites, nature reserves,
national parks, botanical gardens), food (cafes, bakeries, restaurants,
food halls, breweries, wineries), culture (museums, galleries, landmarks,
libraries, places of worship, famous towers, historic sites), entertainment
(theaters, cinemas, nightlife, escape rooms, arcades, stadiums), shopping
(antiques, malls, department stores, gift shops, bookstores, markets),
outdoor recreation (kayak/paddleboard launches, ski pistes, bike rental,
climbing), and relaxation (spas, hot springs, picnic sites, parks). The
full current list is `_OSM_TAGS` in `osm_activities.py`.

`radius_km` defaults to 12, `MAX_RESULTS_PER_DESTINATION` to 100 -- enough
to comfortably reach ~100 real activities per destination in most cities;
a genuinely sparse or remote destination (a national park, a small
mountain town) will honestly come back with fewer, since that's what's
actually there.

### node vs. nwr, and why it matters for query cost

Most tags query plain OSM **nodes** (single points) -- the cheap case.
A handful of tags that are commonly mapped as an area rather than a point
(`leisure=park`, `leisure=nature_reserve`, `leisure=garden`,
`boundary=national_park`, `natural=water`, `tourism=camp_site`,
`leisure=stadium`, `shop=mall`) use the pricier **nwr** (node+way+relation)
selector instead, tracked in `_NWR_TAGS` -- "out center" still gives each
a usable representative coordinate.

This split exists because of a real bug caught during a full 64-destination
ingestion run: querying `nwr` for *every* tag (all ~40 of them, over a
12km radius) made the combined query too expensive for Overpass to fully
evaluate within its own internal timeout. The request still came back
`200 OK` -- Overpass just silently returned an empty or truncated result
once it ran out of time, with no error raised, so a naive read looked like
"this city has no activities" rather than "the query was too expensive."
Scoping `nwr` down to only the tags that actually need it (most
areas-vs-points) fixed it: the same query that returned 0 elements in
58 seconds returned a full 300-element result in 45 seconds once only 8 of
the ~40 tags used `nwr`.

The Overpass-side timeout (`[timeout:55]` in `_OVERPASS_QUERY_TEMPLATE`)
and the client-side `REQUEST_TIMEOUT_SECONDS` (65s, deliberately above the
query's own timeout plus network overhead) are both sized for this
heavier, ~40-tag query -- if the tag list grows further, both may need to
grow too.

Sent as a `POST` with the query as a form body (Overpass's own docs
recommend this over `GET` for anything non-trivial; a `GET` with this much
query data was observed to be flatly rejected with `406 Not Acceptable`)
and a descriptive `User-Agent` header, per Overpass's usage policy.

## Normalization

Duration and indoor/outdoor are documented assumptions per category --
OSM doesn't carry either -- the same pattern as the constants in
[`backpacker_optimizations.md`](backpacker_optimizations.md). Price is
always `0`/unknown: OSM doesn't carry pricing data either, the same honest
gap as the deal connectors' placeholder data (see
[`deal_ingestion_pipeline.md`](deal_ingestion_pipeline.md)) -- though for
free real attractions (parks, viewpoints, monuments) this often happens to
be accurate anyway.

`opening_hours` is only parsed for the simple `"HH:MM-HH:MM"` shape. OSM's
real `opening_hours` grammar is much richer (day ranges, multiple shifts,
holidays) and isn't worth fully implementing here; anything more complex is
left as "open all day" (`None`/`None`), the same fallback the itinerary
scheduler already uses for activities with no listed hours, rather than
attempting to guess wrong.

`location` is a real street address (`"350 5th Avenue, New York, 10118"`)
built from OSM's `addr:housenumber`/`addr:street`/`addr:city`/`addr:postcode`
tags (`_build_address`) when the element has them. Many POIs -- especially
natural features like beaches, viewpoints, and backcountry campsites --
never get a full address in OSM; for those, the honest fallback is a
neighborhood/city label (or the destination's own name), not a fabricated
address standing in for one that doesn't exist.

Elements with no `name` tag are skipped (not presentable as an activity),
counted in the response's `skipped_unnamed`.

`travel_minutes` is estimated from the real haversine distance (see
`optimizations/geo.py`) between the destination's center coordinates and
the POI, at an assumed 25 km/h local travel speed -- another documented
assumption, not a real routing calculation (OSRM, used for the map's
walking routes, isn't used here since these distances span an entire
city, not a single walking leg).

## Upsert / idempotency

Activities gained a nullable `source`/`external_id` pair (`"osm"` /
`"<osm_element_type>/<osm_id>"`), unique together -- the same
`(source, external_id)` upsert-key pattern already used by `Deal`. The
hand-curated seed activities all have `source=None`, and SQL treats
multiple `NULL`s in a unique constraint as distinct from one another, so
they never collide with each other or with real OSM rows. Re-running
ingestion for a destination updates existing OSM-sourced rows instead of
duplicating them.

## Response shape

```json
{
  "inserted": 8,
  "updated": 0,
  "skipped_unnamed": 3,
  "errors": [],
  "by_destination": { "Paris": 11 }
}
```

`POST /api/activities/ingest-osm?destination_id=26` limits ingestion to one
destination; omit `destination_id` to run it for every seeded destination.
At the current ~40-tag, 100-result-per-destination scope, each destination
typically takes 25-90 seconds (a full 64-destination run took roughly
45 minutes end to end during development, including a few destinations
that hit a transient `504` and needed a later retry) -- reasonable for an
occasional manual trigger or a background job, not something to script
into a tight loop given Overpass's fair-use expectations.

## Failure isolation and retry

A failed or timed-out Overpass request for one destination is recorded in
`errors` and doesn't affect any other destination -- the same
per-connector failure isolation as the deal pipeline. Overpass's free
public instance is occasionally slow or briefly rate-limited under load
(observed both `504 Gateway Timeout` and `429 Too Many Requests` during
development, including specifically while building and testing local
activity discovery -- heavy testing from one IP is exactly what trips its
own rate limiting); this is expected of a shared community resource.

`fetch_osm_activities` retries once on a transient failure (429/502/503/504),
honoring a `Retry-After` header if Overpass sends one, else waiting a fixed
short backoff (`RETRY_BACKOFF_SECONDS`). Deliberately just once, not more --
retrying aggressively against a rate limit is counterproductive, and if
Overpass is still unhappy after one measured retry, that's a real signal to
back off and surface the failure rather than keep hammering it. During
sustained heavy load (e.g. a lot of testing in a short window from the same
IP), even this one retry won't always succeed -- that's an inherent
limitation of relying on a free shared API, not a bug in the retry logic.
