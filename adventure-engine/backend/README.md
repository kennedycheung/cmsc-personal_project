# Backend

FastAPI + SQLAlchemy 2.0 backend for the Adventure Arbitrage Engine.
Layered as `app/api/routes` → `app/services` → `app/models` / `app/database`,
with `app/schemas` for Pydantic request/response models and `app/core` for
config/security/time utilities.

## Setup

```bash
cd adventure-engine/backend
cp .env.example .env   # review SECRET_KEY etc. before any real deployment
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first startup the app creates the SQLite database (`adventure.db`),
seeds sample destinations/activities, and runs the deal-ingestion pipeline
— all automatic, no manual `init_db.py` step needed for the app itself
(the standalone `database/init_db.py` script is a separate, secondary tool
that mirrors the same schema for manual SQLite inspection).

- Health check: `http://localhost:8000/api/health`
- Interactive API docs: `http://localhost:8000/docs`

## Testing & linting

```bash
pip install -r requirements-dev.txt
cd ..            # tests run from the adventure-engine/ root (see pytest.ini)
pytest
cd backend && ruff check .
```

See [`../documentation/testing.md`](../documentation/testing.md) for how
the test database and external-API mocking work.

## Configuration

All settings are environment variables (see `.env.example` and
`app/core/config.py`), notably `DATABASE_URL` (SQLite for local dev,
Postgres for production — no code changes needed either way) and
`SECRET_KEY` (signs JWTs; must be overridden in any real deployment).

## Feature documentation

The interesting logic (recommendation scoring, itinerary scheduling,
weather integration, deal ingestion, auth, backpacker-optimization math)
is documented per-feature in [`../documentation/`](../documentation/)
rather than here — see the index in the root `README.md`.
