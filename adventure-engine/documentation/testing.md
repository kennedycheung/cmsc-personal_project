# Testing

## Backend (pytest)

```bash
cd adventure-engine
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r backend/requirements-dev.txt
pytest
```

Config lives in the root [`pytest.ini`](../pytest.ini) (`pythonpath = backend`,
`testpaths = tests/backend`) — run `pytest` from the `adventure-engine/`
root, not from inside `backend/`.

### How the test database works

Tests run against a real temp-file SQLite database (not `:memory:`, which
doesn't play well with connection pooling), created once per test session.
The FastAPI lifespan (create tables, seed sample data, run deal ingestion)
also runs exactly once per session — all of that is local/no-network, so
it's fast.

Each individual test gets its own transactional session, joined to the
connection with SQLAlchemy's `join_transaction_mode="create_savepoint"` and
rolled back afterward. This matters because the app's own route handlers
call `db.commit()` — without the savepoint mode, that commit would end the
outer transaction early and defeat the rollback-based isolation. See
[`tests/backend/conftest.py`](../tests/backend/conftest.py).

This alone isn't sufficient with SQLite, though: Python's `sqlite3` DBAPI
driver manages its own implicit transaction boundaries independently of
SQLAlchemy's explicit `BEGIN`/`SAVEPOINT` control unless that behavior is
disabled. Without disabling it, the driver silently auto-commits the outer
transaction out from under SQLAlchemy at some point during a test — meaning
the *rollback* at teardown has nothing left to undo, and rows written
during a test silently persist into the next one. This surfaced as a very
confusing bug during development: adding OSM activity ingestion (the first
feature to make genuinely fresh multi-row inserts with assertions specific
enough to notice) caused a test to see data left over from a *different*
test, even though this exact isolation setup had "worked" for months —
every existing test happened to either only read data, or write data whose
effects were invisible to leakage (e.g. re-running the idempotent deal
pipeline just re-applies the same values whether or not the prior test's
write was truly rolled back). The real fix is two `event.listens_for`
hooks on the engine in
[`backend/app/database/connection.py`](../backend/app/database/connection.py)
(`isolation_level = None` on connect, plus emitting `BEGIN` explicitly) —
SQLAlchemy's own documented workaround for pysqlite. It's applied to the
engine itself (gated to SQLite only), not just in tests, since it's a
general SQLite transactional-correctness fix, not a test-only concern.

### Why external APIs are mocked

Recommendations, itineraries, and the currency-arbitrage optimization all
call real free APIs (Open-Meteo, Frankfurter) as part of normal request
handling. Real network calls in a test suite are slow, flaky, and can hit
rate limits on repeated CI runs, so `httpx.get` is mocked at the point each
service module calls it (`app.services.weather.httpx.get`,
`app.services.optimizations.currency.httpx.get`) wherever a test exercises
those code paths — see `test_recommendations_and_itineraries.py` and the
currency tests in `test_optimizations.py`. The same file also covers
itineraries planned around a `start_date` (see
[`weather_integration.md`](weather_integration.md#planning-around-a-specific-date)),
mocking both Open-Meteo's regular forecast endpoint and its separate
historical-archive endpoint by branching on the requested URL.

OSM activity ingestion similarly calls a real API (Overpass) as part of its
normal operation — `httpx.post` is mocked the same way in
`test_osm_activities.py`. Local-activity discovery
(`test_local_activities.py`) reuses that same mock, since it calls the same
underlying `fetch_osm_activities`. Geocoding (`test_geocoding.py`) mocks
`httpx.get` against Nominatim the same way weather does against Open-Meteo.

Everything else (destinations, activities, auth, favorites, preferences,
deals, and five of the six backpacker-optimization calculators) is pure
local computation with no network dependency at all.

### Linting

```bash
cd backend
ruff check .
```

## Frontend (Vitest + React Testing Library)

```bash
cd adventure-engine/frontend
npm install
npm test          # single run
npm run test:watch
```

Config lives in [`vite.config.ts`](../frontend/vite.config.ts)'s `test`
block; setup (jest-dom matchers, automatic `cleanup()` between tests) is in
[`src/test/setup.ts`](../frontend/src/test/setup.ts).

Test files are co-located next to what they test (`Component.tsx` +
`Component.test.tsx`), the standard Vitest/React convention, rather than in
a separate mirrored test tree.

### Coverage and scope

The suite covers `BudgetCalculator` (pure client-side calculation logic),
`NotFoundPage` (routing), and `AdventureWizard` (step-by-step navigation
through both the local-adventure and travel-search branches, loading/error
states, and query-param submission, with `services/geocode`,
`services/recommendations`, and `services/localActivities` mocked via
`vi.spyOn` so it exercises the real React Query integration without a
network dependency).

`AdventureMap` is not covered by an automated test: react-leaflet needs
real browser layout/canvas behavior that jsdom doesn't provide, and getting
it working in jsdom tends to require enough mocking that the test stops
proving much. It was instead verified manually in a real browser (see the
map-integration work in an earlier session) and would be a reasonable
candidate for Playwright/browser-based testing if that's added later.

## What's not covered

This is a real test suite for the critical paths, not exhaustive coverage.
Notably untested: the deal connectors' exact placeholder data shapes
(covered indirectly via the ingestion pipeline tests), and most of the
frontend's page-level components beyond `AdventureWizard`. If you extend a
feature, extend its tests alongside it rather than assuming the existing
suite already covers it.
