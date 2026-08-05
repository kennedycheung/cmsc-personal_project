# Activity Discovery Engine (SerpAPI)

Implemented in [`backend/app/services/discovery/`](../backend/app/services/discovery/)
and exposed via `POST /api/discover`.

## Overview

Every other external integration in this app is free and keyless
(Open-Meteo, OSM/Overpass, OSRM, Nominatim, Frankfurter). This feature is
the first exception: it aggregates real search results across 9 of
[SerpAPI](https://serpapi.com)'s engines (Google Events, Google Maps,
Google Maps Directions, TripAdvisor, TripAdvisor Place, TripAdvisor
Reviews, Yelp, Yelp Place, Yelp Reviews) — a paid, keyed service, since
none of those sources have a free API. It's a standalone endpoint,
independent of the existing `Activity`/itinerary system (see
[`itinerary_algorithm.md`](itinerary_algorithm.md)) — nothing here is
persisted or scheduled into a trip.

Set `SERPAPI_KEY` in `.env` to use it (get a key at serpapi.com); without
one, `POST /api/discover` returns `503`.

## The 9 engines, verified live against real API responses

Initially verified by reading SerpAPI's docs, then re-verified against
*real* API responses with a live key — which turned out to matter: several
response shapes differ from what the docs implied (see "Real response
shapes" below). They split cleanly into three roles, which is what drives
this module's structure:

| Engine | `engine=` value | Role |
|---|---|---|
| Google Events | `google_events` | discovery search |
| Google Maps | `google_maps` | discovery search (already includes rating/price/hours inline) |
| Google Maps Directions | `google_maps_directions` | routing — **point-to-point only**, no multi-stop waypoints in one call |
| TripAdvisor | `tripadvisor` | discovery search |
| TripAdvisor Place | `tripadvisor_place` | enrichment |
| TripAdvisor Reviews | `tripadvisor_reviews` | enrichment |
| Yelp | `yelp` | discovery search |
| Yelp Place | `yelp_place` | enrichment |
| Yelp Reviews | `yelp_reviews` | enrichment |

Google Maps isn't separately enriched — its search results already carry
rating/price/hours, unlike TripAdvisor/Yelp's thinner search results which
need their dedicated Place/Reviews engines for that detail.

### Real response shapes (learned from a live key, not docs)

A live smoke test caught several real mismatches between what SerpAPI's
docs summary implied and what the API actually returns — worth recording
so the next person touching this doesn't repeat the same wrong assumptions:

- **`google_maps_directions`** returns `directions` as a flat list of
  *alternative routes for the requested travel mode* (e.g. 3 different
  walking routes), each with plain int `distance` (meters)/`duration`
  (seconds) and `formatted_distance`/`formatted_duration` strings — not
  Google's native Directions API's nested `legs[].distance.{text,value}`
  shape. An undocumented `travel_mode=2` param requests walking-only
  alternatives (matching this app's OSRM walking-route convention
  elsewhere), found by testing since it isn't in SerpAPI's published params.
- **`tripadvisor`** search results live under a `places` key (not
  `results`/`data`), and carry **no coordinates at all** — only a
  free-text `location` string. Same for **`yelp`** search results (no
  `coordinates` field) and **`google_events`**' `venue` object (no
  `latitude`/`longitude`). `merge.py` handles this: it falls back to
  name-similarity-only matching whenever either side lacks coordinates,
  and drops any resulting cluster that never picks up a coordinate from
  *any* member — there's nowhere to place a coordinate-less orphan on a
  map or route. In practice this means a TripAdvisor/Yelp/event-only find
  only survives if it name-matches a Google Maps listing.
- **`yelp`**'s `categories` field is a list of `{"title": ..., "link":
  ...}` objects, not plain strings.
- **`yelp_place`** details live under a `place_results` key (not
  `business`), and photos are a flat list of URL strings under `images`
  (not `photos`).
- **`tripadvisor_reviews`**' review text field is `snippet`, not `text`.
- **`tripadvisor_place`** consistently timed out (60s+) during live
  testing, so its field-parsing in `enrichment.py` is still best-effort/
  unverified — every access there is a no-op rather than a crash if the
  real shape turns out to differ once this engine is reachable again.
- Google Maps' `type` field is a single string; the richer `types` (plural)
  list is what's actually used for interest matching/bucketing now.

### Known limitation: "free" vs. "unknown" price

Google Maps only reports a `price` field (used to compute `price_level`)
for venues where Google has $ /$$/$$$ pricing data — mostly restaurants and
paid attractions. Free public spaces (parks, plazas, viewpoints) usually
have no price field at all rather than an explicit "$0", which is
indistinguishable from "unknown" in this data model. In practice this means
**Best Free** under-reports: a park that's genuinely free won't show up
there unless some source explicitly says so. Not fixed in this pass —
flagging it as a known, data-driven gap rather than a bug to silently paper
over.

## The pipeline

One module per step in [`backend/app/services/discovery/`](../backend/app/services/discovery/),
wired together by `engine.py::discover()`:

1. **`interests.py`** — classifies the request into structured tags from a
   fixed 14-category list (food, museums, nature, shopping, architecture,
   nightlife, festivals, hidden_gems, family, adventure, photography,
   luxury, budget, history). Structured tags passed directly (preferred,
   same chip convention as the rest of this app) win outright; free text is
   a best-effort keyword-table fallback, not an ML/LLM call.
2. **`query_builder.py`** — builds a distinct, tailored query per discovery
   engine — Google Events gets an event-phrased `q` with an optional date
   filter, Google Maps gets a coordinate-anchored `q`, TripAdvisor gets a
   "best X in Y" phrasing with a `ssrc` category filter, Yelp gets split
   `find_desc`/`find_loc` fields. Deliberately not the same string reused
   across engines.
3. **`search_engines.py`** — runs the 4 discovery-search engines
   (`DISCOVERY_ENGINES` registry), isolating a failing engine into a
   warning rather than failing the whole request — same per-source
   isolation spirit as `deals/pipeline.py`'s `CONNECTORS` loop. Adding a
   future source (Viator, GetYourGuide, Ticketmaster, ...) is a new
   registry entry here, not a change to anything downstream.
4. **`merge.py`** — fuzzy-deduplicates results referring to the same real
   place. Two results merge if they're within 50m regardless of name, or
   within 150m *and* `rapidfuzz.fuzz.token_sort_ratio` on their names
   clears 80/100 — handles "Senso-ji" / "Sensō-ji" / "Sensoji Temple"
   collapsing into one `CandidateAttraction`. All three thresholds are
   documented assumptions, same spirit as `itinerary.py`'s `SCORE_WEIGHTS`
   or `osm_activities.py`'s `_OSM_TAGS`.
5. **`enrichment.py`** — fetches Place/Review details for the top
   `MAX_ENRICHED_CANDIDATES` (20) merged candidates only, ranked by a cheap
   popularity proxy (`rating * log(review_count)`) — not every candidate,
   and cached at the `serpapi_client` level (30-minute TTL, same idiom as
   `weather.py`). This cap plus the cache are the concrete cost controls
   for a paid API: without them, one discovery request could mean 4 search
   calls + up to 80 enrichment calls (20 candidates × 4 enrichment
   engines). TripAdvisor's fields win over Yelp's when both provide the
   same one (hours, price, photos) — an explicit precedence, not a silent
   pick.
6. **`ranking.py`** — a weighted score (`SCORE_WEIGHTS`) over interest
   match, distance (haversine from the request origin), rating, popularity
   (log-scaled review count), price fit, hours-data presence, a
   current-events bonus (does this attraction have a live Google Events
   hit merged into it?), and weather suitability (reusing
   `weather.py`'s `is_bad_weather`/`is_good_weather`, not reimplementing
   it).
7. **`buckets.py`** — assigns the ranked list into the 7 named buckets
   (Best Overall, Best Value, Best Hidden Gem, Best Family, Best Evening,
   Best Rainy Day, Best Free) via deterministic predicates. Buckets are
   filled in priority order and a candidate already claimed by a
   higher-priority bucket isn't repeated in a later one — so a sparse
   result set won't show the exact same 3 attractions in every bucket, at
   the cost of a very small candidate pool sometimes leaving a
   lower-priority bucket empty (the same sparse-data honesty tradeoff as
   `itinerary_algorithm.md`'s "sparse activity pools" limitation).
8. **`routing.py`** — chains one Directions call per consecutive pair of
   the "Best Overall" selections (Directions is point-to-point only, so a
   4-stop route means 3 calls, not 1), stitching legs into one ordered
   route with summed duration. A failed leg is skipped rather than failing
   the whole route.

## Cost controls (this is a paid API)

- **Response cache** (`serpapi_client.py`): identical `(engine, params)`
  calls within 30 minutes are free, same TTL-dict idiom as
  `weather.py`/`geocoding.py`.
- **Enrichment cap**: only the top 20 merged candidates by a cheap
  popularity proxy get Place/Review calls; the rest are still usable, just
  with only what the discovery-search engines already returned.
- **Sequential, not parallel**: the 4 discovery-search calls run one after
  another, matching this codebase's synchronous `httpx` usage everywhere
  else (no `asyncio` introduced for this).

## What's deliberately out of scope

- **No frontend page** — this pass is a working, tested backend endpoint
  only (`POST /api/discover`, see `/docs`). A discovery UI is a reasonable
  follow-up once this is validated against a real key.
- **No persistence** — results aren't written to the `Activity` table or
  any other model; this is a standalone discovery call, not an ingestion
  pipeline. A save/favorite action is a natural future addition once
  there's a UI to save from.
- **`tripadvisor_place` enrichment is unverified** — it timed out on every
  live attempt during testing (see above); its parsing is best-effort and
  may need real fixes once that engine responds again.
- Live-tested once against a real key (`POST /api/discover` for Chicago,
  `interests: ["food", "history"]`) — returned real merged results
  (`The Art Institute of Chicago` correctly merged from both `google_maps`
  and `tripadvisor`), a real chained walking route, and correctly isolated
  `google_events` returning zero results as a warning rather than failing
  the request. Every automated test still mocks the HTTP layer (same
  convention as this app's other external-API tests); this one live call
  is what caught and fixed the response-shape mismatches documented above.
