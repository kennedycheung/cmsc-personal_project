# Architecture

This project is structured as a full-stack application with separate frontend and backend modules.

- `frontend/` — React + TypeScript (Vite) UI. See `frontend/README.md`.
- `backend/` — FastAPI application, layered as `app/api/routes` → `app/services` → `app/models`/`app/database`, with `app/schemas` for Pydantic I/O. See `backend/README.md`.
- `database/` — a SQL schema mirror (`schema.sql`) and a standalone `init_db.py` for manual SQLite inspection. The running app doesn't use either directly — SQLAlchemy's `Base.metadata.create_all()` creates the actual tables at startup; `schema.sql` is kept in sync as human-readable documentation.
- `tests/backend/` — pytest suite. Frontend tests are co-located next to the components they test (`Component.test.tsx`) rather than living in a separate `tests/frontend/`.
- `documentation/` — one doc per feature area (see the index in the root `README.md`), plus this file.

All recommendation scoring, itinerary scheduling, deal ingestion, and
weather/currency integration logic lives in `backend/app/services/`. Earlier
scaffold placeholders (`data/`, `algorithms/`, `scrapers/`,
`api_connections/`, plus a broken `backend/app/services/ingest.py`) predated
the real implementation, were never imported by the running app, and have
been removed. A couple of the feature docs still note *why* the real
implementation wasn't built on top of them, for historical context.

## Data flow (typical request)

`frontend/src/services/*.ts` (typed fetch wrapper) → `frontend/src/hooks/*`
(React Query) → component. On the backend: `api/routes/*.py` (FastAPI
router, request validation via `schemas/`) → `services/*.py` (business
logic) → `models/*.py` (SQLAlchemy) / external APIs (Open-Meteo's forecast
and historical-archive endpoints, OSRM, Frankfurter, OpenStreetMap's
Overpass API — all real, free, no-key-required services; see each feature's
doc for which ones it calls and why).

## Persistence

SQLite by default (`DATABASE_URL=sqlite:///./adventure.db`), designed so
switching to Postgres is a one-line env var change with no code changes —
see `documentation/deployment.md`.
