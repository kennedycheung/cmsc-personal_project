# Authentication & Saved User Data

JWT-based auth plus three per-user features: saved adventures, saved
preferences, and favorite destinations.

## Auth flow

- `POST /api/auth/register` — body `{"email", "password"}` (password 8-72
  chars; bcrypt's own hard limit is 72 bytes). 400 if the email is already
  registered. Returns a `TokenResponse` immediately (register logs you in —
  no separate login call needed).
- `POST /api/auth/login` — body `{"email", "password"}`. 401 "Incorrect
  email or password" if either is wrong (deliberately not telling the caller
  which one, standard practice).
- `GET /api/auth/me` — returns the current user (requires auth).

Both register and login return `{"access_token", "token_type": "bearer"}`.
Send it back as `Authorization: Bearer <token>` on every protected request.

### Why HTTPBearer, not OAuth2PasswordBearer

Login here is a plain JSON body, not an OAuth2 form post. `HTTPBearer` (in
[`api/dependencies.py`](../backend/app/api/dependencies.py)) just extracts
and validates the `Authorization: Bearer` header — it doesn't assume a
`tokenUrl` form flow. This also means Swagger UI's "Authorize" dialog shows
a plain paste-a-token field: call `/api/auth/login` via "Try it out", copy
`access_token` from the response, paste it into Authorize.

### Tokens

- HS256, signed with `settings.secret_key` (**must** be overridden via the
  `SECRET_KEY` env var in any real deployment — the `'change-me'` default is
  only for local dev).
- Payload is just `{"sub": "<user_id>", "exp": ...}`.
- Default expiry 24h (`ACCESS_TOKEN_EXPIRE_MINUTES`). There's no refresh
  token or revocation list — out of scope for this app; expired tokens just
  require logging in again.
- Passwords are hashed with bcrypt (`core/security.py`), never stored or
  logged in plain text.

## Saved adventures

`POST /api/saved-adventures/` — body `{destination_id, name, days, budget,
interests}`. This calls the *same* `generate_itinerary()` used by
`GET /api/itineraries/{id}` (see
[`itinerary_algorithm.md`](itinerary_algorithm.md)), then stores the
resulting `ItineraryResponse` as a JSON snapshot
(`SavedAdventure.itinerary_snapshot`) rather than just the input
parameters.

This is a deliberate choice: itinerary generation depends on live weather
(and the deals/activity data could change too), so re-running it later
against the same parameters isn't guaranteed to reproduce the same plan. A
"saved adventure" is the plan as it looked when the user saved it, not a
recipe for regenerating it. `GET /api/saved-adventures/{id}` just replays
the stored snapshot — it doesn't call the itinerary generator again.

- `GET /api/saved-adventures/` — list the current user's saved adventures.
- `GET /api/saved-adventures/{id}` / `DELETE /api/saved-adventures/{id}` —
  404 (not 403) if the adventure doesn't exist *or* belongs to someone else,
  so a request can't be used to probe which IDs exist.

## Saved preferences

One preference profile per user (`max_budget_per_day`, `interests`,
`travel_style`) — no frontend UI persists to these endpoints yet (the
progressive recommendation flow's trip-detail inputs are per-request, not
saved). Wiring a logged-in user's `AdventureWizard` selections to these two
endpoints is a natural next step, not done as part of this change.

- `GET /api/preferences/me` — lazily creates an empty profile on first
  access, so the endpoint always succeeds once authenticated rather than
  404ing until the user has set something.
- `PUT /api/preferences/me` — partial update; only fields present in the
  request body are changed.

## Favorite destinations

A simple user ↔ destination join (`FavoriteDestination`), unique per
`(user_id, destination_id)`.

- `GET /api/favorites/` — list, each entry including the full destination.
- `POST /api/favorites/` — body `{destination_id}`. Idempotent: favoriting
  an already-favorited destination returns the existing favorite rather
  than erroring.
- `DELETE /api/favorites/{destination_id}` — also idempotent: removing a
  destination that isn't currently favorited is a no-op success, not a 404.

## Data model notes

- `User.preferences`/`saved_adventures`/`favorite_destinations` all cascade
  on delete (deleting a user cleans up everything owned by them).
- `Destination` does **not** cascade back to `SavedAdventure` or
  `FavoriteDestination` — those relationships are one-directional (no
  `Destination.saved_by`/`favorited_by`), since nothing else in the app
  currently needs to navigate from a destination to the users who saved or
  favorited it.
