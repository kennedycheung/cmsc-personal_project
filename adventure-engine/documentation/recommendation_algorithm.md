# AdventureScore: Recommendation Algorithm

Implemented in [`backend/app/services/recommendation.py`](../backend/app/services/recommendation.py)
and exposed via `GET /api/recommendations`.

## Overview

AdventureScore ranks every destination currently in the database against an
optional traveler request (`max_budget`, `interests`) and returns the top N
(default 10, matching the "top 10" requirement) as a 0-100 score with a
per-factor breakdown. Everything is computed from the seeded `destinations`
table, plus one live call: a near-term weather outlook per destination from
Open-Meteo (see [`weather_integration.md`](weather_integration.md)).

## Factors

Each factor is normalized to a `[0, 1]` range before weighting.

| Factor | Weight | What it measures |
|---|---|---|
| `budget_fit` | 0.25 | How affordable the destination is against the traveler's `max_budget` per day |
| `interest_match` | 0.25 | Overlap between the traveler's requested interests and the destination's tags |
| `uniqueness` | 0.15 | Curated 0-10 "how one-of-a-kind is this place" rating, stored per destination |
| `cost_efficiency` | 0.15 | How cheap the destination is *relative to the other candidates being ranked* |
| `travel_difficulty` | 0.10 | Inverse of the destination's curated 0-10 "how hard to reach/navigate" rating |
| `weather` | 0.10 | How favorable the next 3 days look (low rain chance, comfortable temperature) |

```
AdventureScore = 100 * Σ (weight_i * factor_i)
```

Weights sum to 1.0, so the score always lands in `[0, 100]`. They live in
`DEFAULT_WEIGHTS` in `recommendation.py` and can be overridden per call via the
`weights` argument to `get_top_recommendations`.

### budget_fit

- No `max_budget` supplied → neutral `0.5` (doesn't help or hurt the ranking).
- `budget_per_day <= max_budget` → `1.0` (fits comfortably).
- Otherwise, falls off linearly with the overage: a destination costing double
  the stated budget scores `0.0`.

### interest_match

- No `interests` supplied → neutral `0.5`.
- Otherwise: `|requested ∩ destination_tags| / |requested|`, capped at `1.0`.
  Interests are matched case-insensitively against the destination's
  comma-separated `interests` column.

### uniqueness

- Directly `destination.uniqueness_score / 10`, clamped to `[0, 1]`. This is a
  static, curated attribute set at seed time — it doesn't depend on the
  traveler's request.

### cost_efficiency

- Min-max normalized *within the current candidate set*: the cheapest
  destination in the set being ranked scores `1.0`, the most expensive scores
  `0.0`. If every candidate costs the same, everyone scores `1.0`.
- This is intentionally relative rather than pinned to a fixed dollar
  reference, so it stays meaningful as the seed dataset grows or changes.

### travel_difficulty

- `1 - destination.travel_difficulty / 10`, clamped to `[0, 1]`. Lower
  difficulty (easier to reach/navigate) scores higher.

### weather

- Fetches a 3-day forecast for the destination's coordinates from Open-Meteo
  and averages: `0.6 * (1 - avg_rain_chance) + 0.4 * temperature_comfort`,
  where temperature comfort peaks at 20°C and falls off linearly.
- If the forecast can't be retrieved (network failure, Open-Meteo down),
  scores a neutral `0.5` rather than penalizing the destination for an
  unrelated outage. Forecasts for all destinations being ranked are fetched
  concurrently (a thread pool) so this doesn't turn one request into 14
  sequential HTTP round-trips.
- Each recommendation also carries a human-readable `weather_summary` string
  (e.g. `"Mainly clear, ~12% avg rain chance over the next 3 days"`), or
  `null` if the forecast was unavailable.

## Ranking

All destinations are scored, sorted by `AdventureScore` descending (ties
broken alphabetically by name for determinism), and the top `top_n` (default
10) are returned with their full score breakdown.

## Example

`GET /api/recommendations?max_budget=150&interests=hiking,scenery`

Returns up to 10 destinations, each as:

```json
{
  "destination": { "id": 1, "name": "Banff National Park", "...": "..." },
  "adventure_score": 78.5,
  "score_breakdown": {
    "budget_fit": 0.68,
    "interest_match": 1.0,
    "uniqueness": 0.7,
    "cost_efficiency": 0.55,
    "travel_difficulty": 0.6,
    "weather": 0.82
  },
  "weather_summary": "Mainly clear, ~8% avg rain chance over the next 3 days"
}
```

## Note on history

An earlier scaffold (`algorithms/scoring.py`, now removed) had a separate,
more generic scorer with an overlapping but different factor set (budget
fit, interest match, distance, uniqueness, adventure level). It was never
imported by the backend — the top-level `algorithms/` package wasn't on
`sys.path` given how the app is actually run, and its factors didn't match
what AdventureScore needed (`cost_efficiency` / `travel_difficulty` /
`weather` vs. `distance` / `adventure_level`) — so AdventureScore was built
fresh in `backend/app/services/recommendation.py` rather than adapted from
it.
