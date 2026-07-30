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

### Why external APIs are mocked

Recommendations, itineraries, and the currency-arbitrage optimization all
call real free APIs (Open-Meteo, Frankfurter) as part of normal request
handling. Real network calls in a test suite are slow, flaky, and can hit
rate limits on repeated CI runs, so `httpx.get` is mocked at the point each
service module calls it (`app.services.weather.httpx.get`,
`app.services.optimizations.currency.httpx.get`) wherever a test exercises
those code paths — see `test_recommendations_and_itineraries.py` and the
currency tests in `test_optimizations.py`.

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
`NotFoundPage` (routing), and `AdventureFinder` (loading/error/retry states
and query-param submission, with the `services/recommendations` module
mocked via `vi.spyOn` so it exercises the real React Query integration
without a network dependency).

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
frontend's page-level components beyond `AdventureFinder`. If you extend a
feature, extend its tests alongside it rather than assuming the existing
suite already covers it.
