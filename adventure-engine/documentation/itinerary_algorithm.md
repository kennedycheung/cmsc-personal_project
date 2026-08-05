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
  against each activity's tag set (its `category` plus its comma-separated
  `tags`, see below) as a proportional overlap, not an exact single-category
  match.
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

Alongside the existing `name`, `price`, and `duration_hours`, activities carry:

- `location` — free-text label of where the activity happens.
- `neighborhood` — the district/suburb the activity sits in, distinct from
  `location`'s full address; populated from OSM's `addr:suburb` tag where
  available, best-effort for hand-curated seed activities. Used only as a
  soft scheduling signal (see `neighborhood_bonus` below), not surfaced as a
  hard filter.
- `category` — a single primary label (e.g. `"museum"`).
- `tags` — comma-separated, richer than `category` (e.g.
  `"museum,culture,history,art"`), so interest matching can score a partial
  overlap instead of requiring the single category to match exactly. Same
  comma-separated-`Text` convention as `Destination.interests` — see
  `Activity.tag_list()`. Populated automatically during OSM ingestion (the
  category plus its Overpass `group` plus a small hand-written synonym
  table, e.g. `"brewery"` also gets `"nightlife"`/`"drinks"`) and for
  hand-curated seed activities via an equivalent seed-category synonym
  table (see `_CATEGORY_SYNONYMS`/`_SEED_CATEGORY_SYNONYMS`).
- `opening_time` / `closing_time` — `"HH:MM"` 24-hour local time; both null
  means "open all day."
- `travel_minutes` — approximate time to reach the activity from a central
  point or the previous stop. This stands in for real geo-routing (no
  lat/long-based routing is modeled here), so "optimize for travel distance"
  means minimizing cumulative travel time across a day's stops. The
  itinerary-editing UI (see [`itinerary_editing.md`](itinerary_editing.md))
  separately recomputes a day's *displayed* total travel time from a real
  OSRM walking route once the user reorders stops, without changing this
  scheduling-time estimate.
- `is_outdoor` — whether bad weather meaningfully hurts this activity (a
  hike, a scenic gondola) as opposed to something weather-resistant (a
  museum, a tasting room, an open-air hot spring you're already wet in).

## Scoring

Each activity gets a score in `[0, 1]`, then a diversity penalty and a
neighborhood bonus are applied on top. `weather_fit` and `time_fit` depend on
the specific day/time being scheduled, so the pool is re-scored after every
single pick (not sorted once per day) — see "Scheduling a day" below.

| Factor | Weight | What it measures |
|---|---|---|
| `interest_match` | 0.30 | Proportion of requested interests found in the activity's tag set (`category` + `tags`), capped at `1.0` — a `"museum,history,art"` activity partially matches a request for just `"history"`. `0.5` (neutral) if no interests were requested |
| `cost_fit` | 0.20 | `1 - price / day_budget`, clamped to `[0, 1]`; free activities always score `1.0` when no budget is given |
| `travel_efficiency` | 0.10 | `1 - travel_minutes / max_travel_minutes` among the destination's candidates — cheaper-to-reach activities score higher |
| `weather_fit` | 0.20 | See below |
| `time_fit` | 0.20 | See below |

### weather_fit

Using that day's Open-Meteo forecast (`bad` = ≥50% rain chance or a
thunderstorm code; `good` = <25% rain chance and clear/mostly clear):

- Bad weather: outdoor activities score `0.15`, weather-resistant ones `1.0`.
- Good weather: outdoor activities score `1.0` (make the most of it),
  weather-resistant ones `0.6`.
- Anything in between: outdoor `0.55`, weather-resistant `0.65`.
- No forecast available for that day: neutral `0.5` for everyone.

### time_fit

A handful of tags/categories have a genuine real-world time-of-day
association, documented in `_MORNING_TAGS`/`_EVENING_TAGS`/`_LATE_NIGHT_TAGS`
(e.g. cafes and hiking lean morning; restaurants and theaters lean evening;
nightlife and breweries lean late-night). The current moment being scheduled
maps to one of four slots (`morning` <12:00, `afternoon` <17:00, `evening`
<21:00, `late_night` beyond that). An activity scores `1.0` if the current
slot is one of its preferred slots, `0.3` if it has preferences but this
isn't one of them, or a neutral `0.6` if it has no documented time
association at all — most tags fall into that last, flexible bucket rather
than being forced into a guessed association.

Activities whose tags associate them *only* with `late_night` (nothing in
`_MORNING_TAGS`/`_EVENING_TAGS`) may be scheduled up to `23:59` instead of
the general `21:00` day cutoff — a category-conditional extension, not a
change to the day window for everything else.

### Diversity penalty and neighborhood bonus

Applied after the four weighted factors above:

- **Diversity penalty**: repeats of the same `category` — counted both
  earlier today and on previous days of the same trip — multiply the score
  by `0.85` per repeat (`0.85 ** repeat_count`). Never a hard block: a
  sparse destination can still reuse a category if nothing else fits, but a
  richer one is nudged toward variety (so four museums in a row only happens
  if nothing else scores competitively).
- **Neighborhood bonus**: a flat `+0.05` when a candidate's `neighborhood`
  matches one already visited earlier in the same day — small on purpose, so
  it only tips close calls toward reducing backtracking rather than
  overriding the primary score.

## Scheduling a day

For each day, starting at `09:00`:

1. Compute the current time slot (see `time_fit` above).
2. Score every not-yet-used candidate that fits the day so far (budget,
   opening/closing hours, and the `21:00`/`23:59` cutoff described above),
   using that day's weather, the current slot, and the categories/
   neighborhoods already picked today.
3. Schedule whichever candidate scores highest; its start time is
   `max(current_time, opening_time)` — the schedule waits for an activity to
   open rather than skipping it outright.
4. Deduct its price from the day's remaining budget, advance `current_time`
   to `end + travel_minutes`, and record its category/neighborhood for the
   next round's diversity/neighborhood scoring.
5. Repeat from step 1. Stop the day after 4 scheduled activities, or as soon
   as no remaining candidate fits at the current time.
6. Remove every scheduled activity from the shared trip-wide pool so later
   days can't repeat it (this step is skipped for a single-day
   "regenerate this day" call — see [`itinerary_editing.md`](itinerary_editing.md)
   — which works from its own excluded-ids list instead).

Re-scoring after every pick (rather than sorting the pool once at the start
of the day, the original approach) is what makes the diversity penalty,
neighborhood bonus, and time-of-day fit actually work: all three depend on
state that only exists once the day is partway built.

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
