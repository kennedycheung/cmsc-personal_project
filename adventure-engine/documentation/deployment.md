# Deployment

## Status: Docker config is written but unverified

The [`backend/Dockerfile`](../backend/Dockerfile),
[`frontend/Dockerfile`](../frontend/Dockerfile), and
[`docker-compose.yml`](../docker-compose.yml) here follow standard, common
patterns (a slim Python image running uvicorn; a multi-stage Node build
served by nginx with an SPA fallback route) but **Docker isn't available in
the environment these were authored in, so `docker build`/`docker compose
up` have not actually been run.** Treat this as a solid starting point to
verify locally, not as a tested deployment path.

## Local Docker Compose

```bash
cd adventure-engine
docker compose up --build
```

- Backend: `http://localhost:8000` (SQLite file persisted in the
  `backend_data` named volume, mounted at `/app/data`)
- Frontend: `http://localhost:8080` (nginx serving the Vite production
  build, `VITE_API_URL` baked in at build time via a Docker build arg)

Override `SECRET_KEY` via an `.env` file at the `adventure-engine/` root
(read automatically by `docker compose`) rather than leaving the
`change-me` default, even for local use.

## SQLite vs. Postgres

The app has been built from the start so this is a one-line change: set
`DATABASE_URL` to a Postgres DSN
(`postgresql://user:pass@host:5432/dbname`) instead of a `sqlite:///` path.
No application code changes are needed -- see `backend/app/database/connection.py`.
SQLite is fine for local dev and small demos; for any real deployment with
concurrent writers, use Postgres (SQLite's single-writer model will
serialize/contend under real traffic).

## Environment variables

Backend (see [`backend/.env.example`](../backend/.env.example)):

| Variable | Notes |
|---|---|
| `DATABASE_URL` | `sqlite:///...` for local/demo, `postgresql://...` for production |
| `SECRET_KEY` | Signs JWTs (see `documentation/authentication.md`). **Must** be a long random value in production -- the `change-me` default is deliberately insecure and PyJWT will warn about short keys |
| `ENVIRONMENT` | Informational (`development`/`production`) |
| `CORS_ORIGINS` | JSON array string of allowed frontend origins |

Frontend (see [`frontend/.env.example`](../frontend/.env.example)):

| Variable | Notes |
|---|---|
| `VITE_API_URL` | Backend API base URL. Baked in at build time (Vite env vars are compile-time, not runtime) -- rebuild the frontend image if this changes |

## Hosting suggestions (not configured here)

No specific hosting provider is wired up -- no deploy credentials or
provider-specific config exist in this repo. Reasonable options once a
provider is chosen:

- **Backend**: any container host that takes a Dockerfile directly (Render,
  Fly.io, Railway) plus a managed Postgres instance from the same
  provider.
- **Frontend**: either the same container approach (the Dockerfile here
  already works standalone), or a static host (Vercel/Netlify) building
  from `frontend/` directly and pointing `VITE_API_URL` at the deployed
  backend -- skipping the nginx container entirely for that path.

Adding an actual deploy step to CI is a reasonable next step once a
provider/target is picked, since it needs provider-specific secrets this
repo doesn't have.

## Repository structure

`adventure-engine/` lives as a subdirectory of a larger git repository
(GitHub: `kennedycheung/cmsc-personal_project`), not as its own repo. This
matters for one thing: GitHub Actions only discovers `.github/workflows/`
at the *actual* repository root, so the CI workflow lives at
`<repo-root>/.github/workflows/ci.yml` (outside `adventure-engine/`
entirely), with every path inside it prefixed `adventure-engine/...` and
the trigger scoped to `paths: ["adventure-engine/**"]` so it only runs when
something in this project actually changes.
