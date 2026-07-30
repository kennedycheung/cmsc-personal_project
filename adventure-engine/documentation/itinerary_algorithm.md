# Itinerary Generation

Implemented in [`backend/app/services/itinerary.py`](../backend/app/services/itinerary.py)
and exposed via `GET /api/itineraries/{destination_id}`.

## Overview

Given a destination and a set of preferences (`days`, `budget`, `interests`),
the endpoint builds a day-by-day plan using only that destination's stored
`activities` rows — no activities invented on the fly. Each activity is used
at most once across the whole itinerary. Scheduling also pulls a live
per-day weather forecast for the destination from Open-Meteo (see
[`weather_integration.md`](weather_integration.md)) and factors it into which
activities get picked for which day.

## Inputs

`GET /api/itineraries/{destination_id}?days=3&budget=600&interests=hiking,food&start_date=2026-09-15`

- `days` (default 3, 1-14) — trip length.
- `budget` (optional) — total trip budget across all days, split evenly per
  day (`day_budget = budget / days`). Omit for an unconstrained budget.
- `interests` (optional, comma-separated) — matched case-insensitively
  against each activity's `category`.
- `start_date` (optional, `YYYY-MM-DD`) — first day of the trip. Omit to
  schedule starting today (the original behavior, using a live 1-16 day
  forecast). With a date supplied, each day of the trip uses a real
  forecast if it falls within the next 16 days, or a historical-average
  "typical weather" estimate if it's farther out — see
  [`weather_integration.md`](weather_integration.md#planning-around-a-specific-date)
  for how that estimate is built. The response flags this explicitly: each
  day's `weather.is_estimate` is `true` when it's an estimate rather than a
  real forecast, and a trip mixing both kinds gets a top-level warning
  calling that out.

## Activity data model

Alongside the existing `name`, `price`, and `duration_hours`, activities now
carry:

- `location` — free-text label of where the activity happens.
- `opening_time` / `closing_time` — `"HH:MM"` 24-hour local time; both null
  means "open all day."
- `travel_minutes` — approximate time to reach the activity from a central
  point or the previous stop. This stands in for real geo-routing (no
  lat/long-based routing is modeled here), so "optimize for travel distance"
  means minimizing cumulative travel time across a day's stops.
- `is_outdoor` — whether bad weather meaningfully hurts this activity (a
  hike, a scenic gondola) as opposed to something weather-resistant (a
  museum, a tasting room, an open-air hot spring you're already wet in).

## Scoring

Each activity gets a score in `[0, 1]`. Three of the four factors are static
per request; `weather_fit` depends on the specific day's forecast, so the
pool is re-ranked fresh for each day rather than sorted once up front:

| Factor | Weight | What it measures |
|---|---|---|
| `interest_match` | 0.4 | `1.0` if the activity's category is in the requested interests, `0.3` if interests were requested but it doesn't match, `0.5` (neutral) if no interests were requested |
| `cost_fit` | 0.25 | `1 - price / day_budget`, clamped to `[0, 1]`; free activities always score `1.0` when no budget is given |
| `travel_efficiency` | 0.15 | `1 - travel_minutes / max_travel_minutes` among the destination's candidates — cheaper-to-reach activities score higher |
| `weather_fit` | 0.20 | See below |

### weather_fit

Using that day's Open-Meteo forecast (`bad` = ≥50% rain chance or a
thunderstorm code; `good` = <25% rain chance and clear/mostly clear):

- Bad weather: outdoor activities score `0.15`, weather-resistant ones `1.0`.
- Good weather: outdoor activities score `1.0` (make the most of it),
  weather-resistant ones `0.6`.
- Anything in between: outdoor `0.55`, weather-resistant `0.65`.
- No forecast available for that day: neutral `0.5` for everyone.

## Scheduling a day

For each day, starting at `09:00` with a `21:00` cutoff:

1. Re-rank the not-yet-used activity pool using that day's weather.
2. Walk the sorted pool. Skip an activity if its price exceeds the day's
   remaining budget.
3. Compute its start time as `max(current_time, opening_time)` — the
   schedule waits for an activity to open rather than skipping it outright.
4. Skip it if `start + duration` would run past its `closing_time` or past
   the `21:00` day cutoff.
5. Otherwise schedule it, deduct its price from the day's remaining budget,
   and advance `current_time` to `end + travel_minutes`.
6. Stop the day after 4 scheduled activities or once no remaining activity
   fits.
7. Remove every scheduled activity from the pool so later days can't repeat
   it.

If the forecast can't be fetched at all (network failure), every day scores
`weather_fit` as neutral and a top-level warning is added:
`"Weather forecast unavailable; scheduling did not account for weather."`

## Response shape

```json
{
  "destination": { "id": 1, "name": "Banff National Park", "...": "..." },
  "days": [
    {
      "day": 1,
      "activities": [
        {
          "activity": { "id": 3, "name": "Johnston Canyon Icewalk", "...": "..." },
          "start_time": "09:00",
          "end_time": "12:00"
        }
      ],
      "total_cost": 40.0,
      "total_travel_minutes": 35.0,
      "weather": {
        "date": "2026-07-30",
        "condition": "Mainly clear",
        "temperature_max": 21.1,
        "temperature_min": 9.6,
        "precipitation_probability": 0.0
      }
    }
  ],
  "total_cost": 40.0,
  "warnings": []
}
```

## Known limitation: sparse activity pools

Several seeded destinations only have one or two stored activities. Since
each activity is used at most once, a multi-day request against a
sparsely-populated destination will legitimately produce empty later days
rather than fabricate filler content. The response's top-level `warnings`
array calls this out per day (e.g. `"Day 2: no remaining stored activities
fit the budget, hours, or day window."`) so the frontend can surface it
instead of silently rendering a blank day.

## Note on history

A standalone itinerary scaffold (`algorithms/itinerary.py`, now removed)
used a hardcoded `DEFAULT_ACTIVITIES` list rather than the database. It was
never used here — this endpoint needs to schedule real stored `Activity`
rows per destination rather than a fixed generic list, and (as with
`recommendation_algorithm.md`) the top-level `algorithms/` package was
never importable from the backend given how the app is actually run.
