# Adventure Arbitrage Engine

A full-stack travel-planning app: destination/activity data, a weather-aware
recommendation and itinerary engine, an OpenStreetMap-based map with real
walking routes, a placeholder deal-ingestion pipeline, JWT auth with saved
adventures/preferences/favorites, and a set of "backpacker arbitrage"
calculators (nearby-airport, overnight-transport, open-jaw routing,
positioning trips, seasonal and currency arbitrage).

## Features

- **Destinations & activities** — seeded sample data (14 destinations,
  ~30 activities) served via a FastAPI + SQLAlchemy backend.
- **Recommendations** ("AdventureScore") — ranks destinations against a
  traveler's budget/interests, factoring in real live weather (Open-Meteo).
  See [`documentation/recommendation_algorithm.md`](documentation/recommendation_algorithm.md).
- **Itinerary generation** — builds a day-by-day plan from stored
  activities only, weather-aware scheduling (an outdoor hike gets bumped to
  the clear day, not the rainy one). See
  [`documentation/itinerary_algorithm.md`](documentation/itinerary_algorithm.md).
- **Map** — Leaflet + OpenStreetMap tiles, with real walking-route
  polylines from OSRM (falls back to a straight line if that's
  unavailable). No Google Maps anywhere.
- **Deal ingestion pipeline** — airline/hotel/tourism connectors
  (placeholder data — no free public API exists for any of these),
  normalized and matched to destinations. See
  [`documentation/deal_ingestion_pipeline.md`](documentation/deal_ingestion_pipeline.md).
- **Auth & saved data** — JWT register/login, saved adventures (itinerary
  snapshots), saved preferences, favorite destinations. See
  [`documentation/authentication.md`](documentation/authentication.md).
- **Backpacker optimizations** — six cost/time calculators, each with a
  worked mathematical explanation before its implementation. Currency
  arbitrage uses a real live API (Frankfurter/ECB rates); the rest are
  local math over curated/seeded data. See
  [`documentation/backpacker_optimizations.md`](documentation/backpacker_optimizations.md).

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

See [`documentation/deployment.md`](documentation/deployment.md) — this
config is written but not yet verified in a real Docker environment.

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
| [`recommendation_algorithm.md`](documentation/recommendation_algorithm.md) | AdventureScore ranking |
| [`itinerary_algorithm.md`](documentation/itinerary_algorithm.md) | Day-by-day scheduling |
| [`weather_integration.md`](documentation/weather_integration.md) | Open-Meteo integration |
| [`deal_ingestion_pipeline.md`](documentation/deal_ingestion_pipeline.md) | Airline/hotel/tourism deal connectors |
| [`authentication.md`](documentation/authentication.md) | JWT auth, saved adventures/preferences/favorites |
| [`backpacker_optimizations.md`](documentation/backpacker_optimizations.md) | The six arbitrage calculators, math first |
| [`testing.md`](documentation/testing.md) | How and why the test suite is structured the way it is |
| [`deployment.md`](documentation/deployment.md) | Docker, env vars, Postgres migration path |
| [`development_notes.md`](documentation/development_notes.md) | Short-form dev conventions |

## Known gaps

- No auth UI on the frontend yet (register/login/saved-preferences exist
  as backend endpoints only) — `TripPreferenceForm` is a local-only preview,
  and says so.
- Docker config is untested (no Docker available in the environment this
  was built in).
- `npm audit` flags two moderate advisories (Vite/esbuild's dev-server-only
  issue, and a React Router open redirect) where the real fix requires a
  breaking major-version upgrade on each — deliberately not force-upgraded
  without validating the app still works afterward.
