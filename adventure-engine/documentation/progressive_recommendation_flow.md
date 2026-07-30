# Progressive Recommendation Flow

Implemented in [`frontend/src/components/AdventureWizard.tsx`](../frontend/src/components/AdventureWizard.tsx)
(frontend) and `backend/app/services/geocoding.py`, `travel_time.py`,
`local_activities.py`, plus extensions to `recommendation.py` (backend).

## Overview

This replaced the original budget-first entry point (a single form asking
for max budget/day and interests, then a ranked destination list) with a
progressive flow that narrows down the trip the way a person actually
plans one: where am I, how much time do I have, and only then, what am I
looking for.

```
1. Where are you starting from?  (geocoded to coordinates)
2. How much time do you have?    (one of 8 buckets, 2 hours -> 2 weeks)
3. [only for >=1 day] Stay local, day trip, overnight, or anywhere?
4. Trip details                  (categories for a local adventure;
                                   budget/interests for a travel search)
5. Results
```

Steps under a day skip step 3 entirely and go straight into "local
adventure" mode — real nearby activities, not a destination search. There
are no flights or hotels in that mode by design.

## Step 1: starting location

`GET /api/geocode?query=Chicago` resolves free-text input (a city or an
airport name/code -- "JFK airport" works the same as "Chicago") to
coordinates via [Nominatim](https://nominatim.openstreetmap.org/), OSM's
free, keyless geocoding API -- the same "real free API" pattern already
used for weather, routing, and activity discovery elsewhere in this app.
Implemented in `backend/app/services/geocoding.py`.

Nominatim's usage policy asks for a descriptive `User-Agent` and no more
than one request per second from a single client; both are enforced
(a client-side throttle tracks the last call and sleeps if needed, the
same spirit as Overpass's usage policy already respected by
`osm_activities.py`). Results are cached for an hour -- a place's
coordinates don't change.

"Use my current GPS location" isn't in the UI -- just the manual city/
airport text entry. A real implementation needs the browser's Geolocation
API wired up on the frontend, deliberately out of scope for this pass; a
disabled placeholder button was tried first and removed since a
non-functional control is worse than no control.

## Step 2: available time

Eight buckets (`TimeBucket` enum in `backend/app/services/travel_time.py`,
mirrored as plain strings in `frontend/src/constants.ts`): 2 hours, half
day, full day, weekend, 3-4 days, 5-7 days, 1 week, 2 weeks. Sent as an
opaque string to the backend, which owns the distance mapping -- the
frontend never computes a distance itself.

| Bucket | Max distance | Rationale |
|---|---|---|
| 2 hours / half day | 15 km | current city only |
| full day | 150 km | nearby cities |
| weekend | 800 km | driving distance or short flight |
| 3-4 days | 2000 km | wider domestic range |
| 5-7 days / 1 week / 2 weeks | unconstrained | domestic or international |

Every distance here is a documented assumption, not a measured fact --
same spirit as `optimizations/constants.py`'s constants table.

## Step 3: how far (>=1 day only)

Stay local / day trip / overnight trip / anywhere within budget
(`TravelScope` enum, same file). This refines, rather than replaces, the
bucket's distance:

```
resolve_max_distance_km(bucket, scope):
  stay_local             -> 50 km, overriding the bucket entirely
  anywhere_within_budget -> unconstrained, overriding the bucket entirely
  day_trip / overnight   -> the bucket's own default distance
```

Buckets under a day skip this question entirely (per the product spec --
a local adventure has no "how far" choice to make).

## Step 4a: local adventure discovery

`GET /api/local-activities?latitude=&longitude=&radius_km=&groups=` --
implemented in `backend/app/services/local_activities.py`, a **live,
non-persisted** query, unlike the destination-scoped OSM ingestion
pipeline (`osm_activities.py`, see
[`osm_activity_ingestion.md`](osm_activity_ingestion.md)). There's no
seeded `Destination` row for an arbitrary origin point to attach activity
rows to, so nothing is written to the database -- results are returned
directly.

This reuses and heavily expands `osm_activities.py`'s tag taxonomy and
Overpass query machinery (`_OSM_TAGS`, `_build_query`,
`normalize_osm_element_raw`) rather than duplicating it, now covering
seven groups instead of the ingestion pipeline's flat category list:

| Group | Example OSM tags |
|---|---|
| Nature | beaches, lakes, waterfalls, viewpoints, campsites, nature reserves, national parks, botanical gardens |
| Food | cafes, bakeries, restaurants, food halls, breweries, wineries, markets |
| Culture | museums, galleries, landmarks, libraries, historic sites |
| Entertainment | theaters, cinemas, nightlife, escape rooms, arcades, stadiums |
| Shopping | antique stores, malls, bookstores |
| Outdoor recreation | kayak/paddleboard put-ins, ski pistes, bike rental (cycling proxy), climbing |
| Relaxation | spas, hot springs, picnic sites, parks |

The Overpass query switched from `node`-only to `nwr` (node+way+relation)
as part of this expansion: area-based features like parks, nature
reserves, and national park boundaries are frequently tagged on ways or
relations with no standalone point, and `out center` gives each a usable
representative coordinate either way.

**Deliberately excluded**: concerts, festivals, sporting events, and
seasonal/holiday events. OSM models permanent venues (a stadium, a
theater), not what's scheduled there on a given date -- there's no
keyless way to get real event listings. Real event data needs a keyed API
(Ticketmaster, Eventbrite), which is a reasonable future addition once
that tradeoff is worth making, not something this pass attempts to fake.
Also excluded: food trucks (too transient to be meaningfully tagged) and
general "scenic drives" (a route, not a point).

## Step 4b / 5: distance-constrained recommendations

For >=1-day trips, `recommendation.py`'s `get_top_recommendations` gained
three optional parameters: `origin_lat`, `origin_lon`, `max_distance_km`.
When supplied, destinations farther than that (great-circle distance via
`optimizations/geo.py::haversine_km`, already used by the open-jaw
calculator) are excluded **before** AdventureScore runs -- a hard filter,
not a soft factor, since the product spec is explicit that travel
distance should be constrained by available time, not just nudge the
ranking. Omitting the origin preserves the original unfiltered behavior
(nothing else that calls this function breaks).

`GET /api/recommendations/` also accepts `time_bucket`/`travel_scope`
directly and resolves the distance server-side via
`resolve_max_distance_km` -- the frontend doesn't duplicate the mapping
table; an explicit `max_distance_km` still wins if both are given.

## What's deliberately not built yet

Two real, substantial pieces from the product spec are scoped but not
implemented in this pass:

- **Transportation cost estimation** (origin -> destination, by distance
  and mode, party-size-aware sharing) -- there's no free real fare API
  (same gap as the deal ingestion pipeline), so this needs a documented-
  assumption cost curve in the style of the existing backpacker-
  optimization calculators.
- **Total-trip budget allocation** (total budget minus transportation,
  split across lodging/food/activities/local-transport/contingency,
  party-size-aware) -- replaces the current "max budget per day" input
  with a computed effective per-day budget fed into the existing
  `_score_budget_fit`/`_score_cost_efficiency` factors.

Until those land, the >=1-day path still asks for a max budget/day
directly (todays's simpler model), and the remaining trip-detail fields
from the product spec (avoid-list, travel style, comfort level,
transportation preference, date flexibility) aren't wired in yet either.
