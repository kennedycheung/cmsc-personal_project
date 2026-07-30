# Weather Integration (Open-Meteo)

Implemented in [`backend/app/services/weather.py`](../backend/app/services/weather.py).
Consumed by [`recommendation_algorithm.md`](recommendation_algorithm.md) (destination-level
scoring) and [`itinerary_algorithm.md`](itinerary_algorithm.md) (per-day scheduling).

## Why Open-Meteo

Free, no API key, no signup, and a stable JSON contract — a reasonable choice
for a portfolio project that shouldn't require secrets to run locally.

## Request shape

```
GET https://api.open-meteo.com/v1/forecast
    ?latitude={lat}&longitude={lon}
    &daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max
    &timezone=auto
    &forecast_days={1-16}
```

`forecast_days` is clamped to `[1, 16]` — Open-Meteo's free forecast covers
at most 16 days, which comfortably covers the itinerary endpoint's max of 14.

## WMO weather codes

Open-Meteo's `weathercode` field uses the WMO numeric codes (0 = clear sky,
1-3 = clear/partly cloudy/overcast, 45-48 = fog, 51-57 = drizzle, 61-67 =
rain, 71-77 = snow, 80-86 = showers, 95-99 = thunderstorm). `weather.py` maps
each code to a short human-readable label (`_describe`) and exposes two
booleans used throughout the scoring code instead of raw thresholds scattered
everywhere:

- `is_bad_weather(day)` — ≥50% precipitation probability, or a thunderstorm
  code (≥95).
- `is_good_weather(day)` — <25% precipitation probability and a
  clear/mostly-clear code (≤2).

Anything in between is "marginal" and handled as a middle case by callers.

## Caching

Forecasts are cached in-process for 30 minutes, keyed by
`(round(lat, 2), round(lon, 2), forecast_days)`. Weather doesn't change
meaningfully faster than that, and it keeps repeated recommendation/itinerary
requests from re-hitting Open-Meteo for the same destination.

## Batching multi-destination requests

The recommendations endpoint scores every seeded destination on every
request. Fetching each one's forecast as a separate call -- even in
parallel -- turned out to be a real problem during testing: Open-Meteo's
free tier rate-limits bursts of concurrent requests from one IP (observed
`429 Too Many Requests` on roughly 3 of 14 destinations when fetched via an
8-worker thread pool).

Open-Meteo actually supports multiple locations in a single request: pass
comma-separated `latitude`/`longitude` lists and it returns one forecast
object per location, in the same order, in one response (a bare object for
one location, a JSON array for more than one). `get_forecasts_batch` uses
this instead of any concurrency -- one HTTP round-trip covers every
destination that isn't already cached, and returns a plain
`{destination_id: forecast_or_None}` map.

## Failure handling

`get_forecast` raises `WeatherUnavailableError` on any network failure,
non-2xx response, or unparseable payload. Every caller catches this and
degrades to a neutral score rather than letting a third-party outage break
recommendations or itinerary generation:

- Recommendation scoring: `weather` factor scores a neutral `0.5` and
  `weather_summary` is `null` for that destination.
- Itinerary generation: every day's `weather_fit` factor scores a neutral
  `0.5`, the response's `weather` field is `null` for each day, and a
  top-level warning is added once: `"Weather forecast unavailable;
  scheduling did not account for weather."`

Bogus coordinates (e.g. out of range) are handled the same way — Open-Meteo
returns an error response, which `get_forecast` treats like any other
failure.
