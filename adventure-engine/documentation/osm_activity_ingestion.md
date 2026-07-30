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
request) for nearby OSM nodes matching any of:

| OSM tag | Mapped category | Default duration | Outdoor? |
|---|---|---|---|
| `tourism=museum` | culture | 2.0h | no |
| `tourism=gallery` | art | 1.5h | no |
| `tourism=aquarium` | wildlife | 2.0h | no |
| `tourism=zoo` | wildlife | 3.0h | yes |
| `tourism=theme_park` | adventure | 4.0h | yes |
| `tourism=viewpoint` | scenery | 0.75h | yes |
| `tourism=attraction` | sightseeing | 1.5h | yes |
| `leisure=park` | relaxation | 1.5h | yes |
| `historic=monument` | history | 1.0h | yes |
| `historic=castle` | history | 1.5h | yes |
| `historic=ruins` | history | 1.0h | yes |
| `natural=beach` | relaxation | 2.0h | yes |

`radius_km` defaults to 5 -- large enough to cover a city center's worth of
attractions, small enough that the combined 12-tag query reliably completes
within Overpass's own query timeout even under load. Sent as a `POST` with
the query as a form body (Overpass's own docs recommend this over `GET` for
anything non-trivial; a `GET` with this much query data was observed to be
flatly rejected with `406 Not Acceptable`) and a descriptive `User-Agent`
header, per Overpass's usage policy.

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
destination; omit `destination_id` to run it for every seeded destination
(64 individual Overpass queries -- reasonable for an occasional manual
trigger, not something to script into a tight loop given Overpass's
fair-use expectations).

## Failure isolation

A failed or timed-out Overpass request for one destination is recorded in
`errors` and doesn't affect any other destination -- the same
per-connector failure isolation as the deal pipeline. Overpass's free
public instance is occasionally slow or briefly rate-limited under load
(observed both `504 Gateway Timeout` and `429 Too Many Requests` during
development); this is expected of a shared community resource and the
pipeline degrades to reporting the error rather than crashing the request.
