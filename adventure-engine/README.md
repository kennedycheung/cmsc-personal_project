# Adventure Arbitrage Engine

A full-stack travel-planning app: a progressive recommendation flow that
starts from where you are and how much time you have, destination/activity
data, a weather-aware recommendation and itinerary engine, an
OpenStreetMap-based map with real walking routes, a placeholder
deal-ingestion pipeline, JWT auth with saved adventures/preferences/
favorites, and a set of "backpacker arbitrage" calculators (nearby-airport,
overnight-transport, open-jaw routing, positioning trips, seasonal and
currency arbitrage).

## Features

- **Progressive recommendation flow** — starts from "where are you
  starting from?" and "how much time do you have?" rather than budget
  first; branches into a live local-activity search (real nearby places
  via OpenStreetMap, no flights/hotels) for trips under a day, or a
  distance-constrained destination search for longer trips. See
  [`documentation/progressive_recommendation_flow.md`](documentation/progressive_recommendation_flow.md).
- **Destinations & activities** — 64 hand-curated destinations (major US
  cities plus the international destinations Americans most commonly
  travel to, alongside the original seed set), ~90 hand-curated activities,
  served via a FastAPI + SQLAlchemy backend. Supplemented with thousands
  more real, live-sourced activities pulled from OpenStreetMap — real
  addresses, up to ~100 per destination where that much real data exists
  — see
  [`documentation/osm_activity_ingestion.md`](documentation/osm_activity_ingestion.md).
- **Recommendations** ("AdventureScore") — ranks destinations against a
  traveler's budget/interests and (optionally) distance from a starting
  location, factoring in real live weather (Open-Meteo). See
  [`documentation/recommendation_algorithm.md`](documentation/recommendation_algorithm.md).
- **Itinerary generation** — builds a day-by-day plan from stored
  activities only, weather-aware scheduling (an outdoor hike gets bumped to
  the clear day, not the rainy one), time-of-day-aware (cafes lean morning,
  nightlife leans late-night), favoring variety over stacking the same
  category and softly clustering same-neighborhood stops, multi-tag interest
  matching (partial overlaps score, not just one exact category), optionally
  planned around a specific future travel date (real forecast within 16
  days, a historical-average estimate farther out). See
  [`documentation/itinerary_algorithm.md`](documentation/itinerary_algorithm.md).
- **Map** — Leaflet + OpenStreetMap tiles, with real walking-route
  polylines from OSRM (falls back to a straight line if that's
  unavailable), hidden-by-default activity markers once an itinerary
  exists (with a toggle to reveal them), and click-to-select syncing
  between the map and the activity/itinerary lists. No Google Maps
  anywhere.
- **Interactive itinerary editing** — drag-to-reorder, remove, swap for a
  tag-ranked alternative, or regenerate just one day, all client-side until
  saved; real OSRM travel time recalculated after a reorder. See
  [`documentation/itinerary_editing.md`](documentation/itinerary_editing.md).
- **Deal ingestion pipeline** — airline/hotel/tourism connectors
  (placeholder data — no free public API exists for any of these),
  normalized and matched to destinations. See
  [`documentation/deal_ingestion_pipeline.md`](documentation/deal_ingestion_pipeline.md).
- **Auth & saved data** — JWT register/login (now with a frontend login/
  register UI, not just backend endpoints), saved adventures (itinerary
  snapshots), saved preferences, favorite destinations. See
  [`documentation/authentication.md`](documentation/authentication.md).
- **Backpacker optimizations** — eight cost/time calculators, each with a
  worked mathematical explanation before its implementation, including
  origin→destination transportation cost estimation and total-trip budget
  allocation. Currency arbitrage uses a real live API (Frankfurter/ECB
  rates); the rest are local math over curated/seeded data. See
  [`documentation/backpacker_optimizations.md`](documentation/backpacker_optimizations.md).
- **Activity Discovery Engine** — aggregates real search results across 9
  SerpAPI engines (Google Events/Maps/Directions, TripAdvisor + Place +
  Reviews, Yelp + Place + Reviews), fuzzy-deduplicates near-duplicate
  attractions, enriches and ranks them, and groups the result into 7 named
  recommendation buckets (Best Overall, Best Value, Best Hidden Gem, Best
  Family, Best Evening, Best Rainy Day, Best Free) plus a chained route.
  The first paid/keyed integration in this app — needs a `SERPAPI_KEY`. See
  [`documentation/activity_discovery_engine.md`](documentation/activity_discovery_engine.md).

## Structure

- `frontend/` — React + TypeScript (Vite), React Query, React Router, Leaflet.
- `backend/` — FastAPI + SQLAlchemy 2.0, layered as `api/routes` → `services` → `models`/`database`.
- `database/` — SQL schema mirror + a standalone SQLite init script (see note below).
- `tests/backend/` — pytest suite (see [`documentation/testing.md`](documentation/testing.md)); frontend tests are co-located next to the components they test.
- `documentation/` — architecture, algorithm, and process docs (linked throughout this file).

## Quickstart

### Backend

```bash
cd adventure-engine/backend
cp .env.example .env   # review/adjust SECRET_KEY etc. before any real deployment
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first startup this creates the SQLite database, seeds sample
destinations/activities, and runs the deal-ingestion pipeline. Visit
`http://localhost:8000/api/health` to confirm it's up, or
`http://localhost:8000/docs` for interactive API docs.

### Frontend

```bash
cd adventure-engine/frontend
cp .env.example .env   # points at the backend above by default
npm install
npm run dev
```

Open `http://localhost:5173`.

### Docker (alternative to the above)

```bash
cd adventure-engine
docker compose up --build
```

See [`documentation/deployment.md`](documentation/deployment.md) for details
-- this has been verified with a real `docker compose up --build`.

## Testing

```bash
# backend, from adventure-engine/
pip install -r backend/requirements-dev.txt
pytest

# frontend
cd frontend && npm test
```

Full rationale (including why external APIs are mocked in tests) in
[`documentation/testing.md`](documentation/testing.md).

## Documentation index

| Doc | Covers |
|---|---|
| [`architecture.md`](documentation/architecture.md) | Repo layout |
| [`progressive_recommendation_flow.md`](documentation/progressive_recommendation_flow.md) | Origin/time/branch wizard, live local-activity discovery |
| [`recommendation_algorithm.md`](documentation/recommendation_algorithm.md) | AdventureScore ranking |
| [`itinerary_algorithm.md`](documentation/itinerary_algorithm.md) | Day-by-day scheduling |
| [`itinerary_editing.md`](documentation/itinerary_editing.md) | Map selection UX and interactive itinerary editing |
| [`weather_integration.md`](documentation/weather_integration.md) | Open-Meteo integration, incl. date-based planning |
| [`osm_activity_ingestion.md`](documentation/osm_activity_ingestion.md) | Real, live-sourced activities from OpenStreetMap |
| [`deal_ingestion_pipeline.md`](documentation/deal_ingestion_pipeline.md) | Airline/hotel/tourism deal connectors |
| [`authentication.md`](documentation/authentication.md) | JWT auth, saved adventures/preferences/favorites |
| [`backpacker_optimizations.md`](documentation/backpacker_optimizations.md) | The eight arbitrage calculators, math first |
| [`activity_discovery_engine.md`](documentation/activity_discovery_engine.md) | Multi-engine SerpAPI aggregation, fuzzy dedup, ranking, recommendation buckets |
| [`testing.md`](documentation/testing.md) | How and why the test suite is structured the way it is |
| [`deployment.md`](documentation/deployment.md) | Docker, env vars, Postgres migration path |
| [`development_notes.md`](documentation/development_notes.md) | Short-form dev conventions |

## Known gaps

- Transportation-cost estimation and total-trip budget allocation now exist
  as standalone calculators (`backpacker_optimizations.md` §7-8), but
  aren't wired into `recommendation.py`'s core `AdventureScore` ranking
  yet -- the >=1-day path still asks for a max budget/day directly rather
  than deriving an effective per-day budget from a total trip budget minus
  transportation. That wiring needs a per-candidate-destination effective
  budget (each destination is a different distance from the origin), which
  is a bigger change to the ranking loop than adding the calculators
  themselves was.
- Real-time event listings (concerts, festivals, sporting events) aren't
  available in local-activity discovery -- OSM has the venues, not the
  schedule; real event data needs a keyed API (Ticketmaster/Eventbrite).
- A handful of destinations (Sedona, Kyoto, Queenstown, Bali, Patagonia, San
  Francisco, Miami, New Orleans, Nashville, Honolulu, and a couple others)
  still have thinner OSM activity coverage than the rest -- their ingestion
  runs kept hitting Overpass `429`/`504`s from repeated heavy testing
  against one IP during the sessions that built this feature (most of the
  64 seeded destinations now have close to the ~100-per-city cap).
  Re-running `POST /api/activities/ingest-osm?destination_id=<id>` for each
  once Overpass's rate limit has cooled off will fill these in; it's
  idempotent, safe to retry anytime.
- The Activity Discovery Engine (`POST /api/discover`) now has a frontend
  page (`/discover`) and has been live-tested against a real SerpAPI key
  (see `activity_discovery_engine.md`'s "Real response shapes" section for
  what that live test caught and fixed). `tripadvisor_place` enrichment
  specifically is still unverified -- it timed out on every live attempt.
  Every automated test still mocks the HTTP layer, same as this app's other
  external-API tests.
- `neighborhood` (used to softly cluster an itinerary day's stops) is
  best-effort, not exhaustive: it's populated from OSM's `addr:suburb` tag,
  which many points of interest simply don't have, and from hand-curated
  seed activities' existing `location` label as a stand-in. Missing
  neighborhoods just skip the clustering bonus for that activity rather than
  being treated as an error.
- `npm audit` flags 4 advisories (3 moderate, 1 high) across two dependency
  chains — Vite/esbuild (dev-server-only issues, e.g. path traversal in
  optimized deps handling) and React Router (open redirect / SSR hydration
  issues) — where the real fix requires a breaking major-version upgrade on
  each (Vite 5→8, React Router 6→7) — deliberately not force-upgraded
  without validating the app still works afterward.
