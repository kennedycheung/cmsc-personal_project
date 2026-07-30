# Frontend

React 18 + TypeScript (Vite), React Query for data fetching, React Router,
Leaflet/react-leaflet for the map.

## Setup

```bash
cd adventure-engine/frontend
cp .env.example .env   # points at http://localhost:8000/api by default
npm install
npm run dev
```

Open `http://localhost:5173`. The backend (see `../backend/README.md`)
needs to be running separately for any of the data-driven pages to work.

## Scripts

```bash
npm run dev        # dev server
npm run build       # tsc typecheck + production build to dist/
npm run preview     # preview the production build locally
npm test            # run the Vitest suite once
npm run test:watch  # Vitest in watch mode
```

## Structure

- `src/pages/` — route-level components (`HomePage`, `DestinationPage`, `NotFoundPage`).
- `src/components/` — `AdventureWizard`, `AdventureMap`.
- `src/hooks/` — React Query hooks wrapping the service layer.
- `src/services/` — typed API client functions (one module per backend resource) plus `routing.ts` for the OSRM walking-route calls.
- `src/test/setup.ts` — Vitest/Testing Library setup (imported via `vite.config.ts`'s `test.setupFiles`).

Test files are co-located next to what they test
(`Component.tsx` + `Component.test.tsx`) rather than mirrored into a
separate test tree — see [`../documentation/testing.md`](../documentation/testing.md).

## Known gap

`AdventureWizard`'s trip-detail inputs are per-request only, not saved —
the backend has real `/api/preferences` and `/api/favorites` endpoints
(see `../documentation/authentication.md`) but there's no login/register UI
here yet to actually call them with. Wiring that up is a reasonable next
step, not something silently pretended to work.
