"""Open-Meteo forecast client: free, no API key, used to weight itinerary
scheduling and recommendation scoring by forecasted weather.

See documentation/weather_integration.md for the endpoint shape, the WMO
weather-code mapping, and the good/bad weather thresholds used elsewhere.
"""

import time
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
REQUEST_TIMEOUT_SECONDS = 5.0
CACHE_TTL_SECONDS = 1800  # 30 minutes -- forecasts don't meaningfully change faster than this.
TYPICAL_CACHE_TTL_SECONDS = 86400  # historical climate data is effectively static day to day.
TYPICAL_LOOKBACK_YEARS = 5
DAILY_FIELDS = "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
# The archive API reports actual measured rainfall, not a forecast probability.
ARCHIVE_DAILY_FIELDS = "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum"

# WMO Weather interpretation codes, as used by Open-Meteo's `weathercode` field.
_WEATHER_CODE_LABELS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass
class DayForecast:
    date: str
    weather_code: int
    condition: str
    temperature_max: float
    temperature_min: float
    precipitation_probability: float
    # True when this is a historical-average "typical weather" estimate
    # (see get_typical_weather_for_dates) rather than a real Open-Meteo
    # forecast -- callers/API consumers should surface this distinction
    # rather than presenting an estimate as if it were a prediction.
    is_estimate: bool = False


class WeatherUnavailableError(Exception):
    """Raised when Open-Meteo can't be reached or returns an unusable response."""


_cache: dict[tuple[float, float, int], tuple[float, list[DayForecast]]] = {}


def _describe(weather_code: int) -> str:
    return _WEATHER_CODE_LABELS.get(weather_code, "Unknown")


def _parse_daily(daily: dict) -> list[DayForecast]:
    return [
        DayForecast(
            date=date,
            weather_code=code,
            condition=_describe(code),
            temperature_max=temp_max,
            temperature_min=temp_min,
            precipitation_probability=precip_prob,
        )
        for date, code, temp_max, temp_min, precip_prob in zip(
            daily["time"],
            daily["weathercode"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_probability_max"],
        )
    ]


def is_bad_weather(day: DayForecast) -> bool:
    """Rain/storm severe enough to meaningfully hurt an outdoor activity."""
    return day.precipitation_probability >= 50 or day.weather_code >= 95


def is_good_weather(day: DayForecast) -> bool:
    """Clear/mostly clear with low rain chance -- a day worth spending outdoors."""
    return day.precipitation_probability < 25 and day.weather_code <= 2


def get_forecast(latitude: float, longitude: float, days: int) -> list[DayForecast]:
    """Fetch a single location's daily forecast, using a short-lived in-memory cache.

    Raises WeatherUnavailableError on any network/parse failure -- callers are
    expected to catch this and degrade to neutral scoring rather than let a
    flaky third-party API break itinerary/recommendation generation.
    """
    forecast_days = min(max(days, 1), 16)
    cache_key = (round(latitude, 2), round(longitude, 2), forecast_days)

    cached = _cache.get(cache_key)
    if cached is not None and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        response = httpx.get(
            OPEN_METEO_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": DAILY_FIELDS,
                "timezone": "auto",
                "forecast_days": forecast_days,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        forecast = _parse_daily(response.json()["daily"])
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise WeatherUnavailableError(str(exc)) from exc

    _cache[cache_key] = (time.monotonic(), forecast)
    return forecast


def get_forecasts_batch(
    coordinates: list[tuple[int, float, float]], days: int
) -> dict[int, list[DayForecast] | None]:
    """Fetch forecasts for many (id, latitude, longitude) triples.

    Open-Meteo accepts comma-separated latitude/longitude lists and returns
    one forecast per location in a single request -- used here instead of N
    separate calls (even in parallel) because Open-Meteo's free tier rate-
    limits bursts of concurrent requests from one IP (observed 429s at ~8
    simultaneous requests during testing). Never raises: any destination
    whose forecast can't be resolved maps to None.
    """
    if not coordinates:
        return {}

    forecast_days = min(max(days, 1), 16)
    results: dict[int, list[DayForecast] | None] = {}
    to_fetch: list[tuple[int, float, float]] = []

    for destination_id, lat, lon in coordinates:
        cache_key = (round(lat, 2), round(lon, 2), forecast_days)
        cached = _cache.get(cache_key)
        if cached is not None and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
            results[destination_id] = cached[1]
        else:
            to_fetch.append((destination_id, lat, lon))

    if not to_fetch:
        return results

    try:
        response = httpx.get(
            OPEN_METEO_URL,
            params={
                "latitude": ",".join(str(lat) for _, lat, _ in to_fetch),
                "longitude": ",".join(str(lon) for _, _, lon in to_fetch),
                "daily": DAILY_FIELDS,
                "timezone": "auto",
                "forecast_days": forecast_days,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        # Open-Meteo returns a bare object for a single location and a list
        # (one entry per location, same order as the request) for multiple.
        entries = payload if isinstance(payload, list) else [payload]

        for (destination_id, lat, lon), entry in zip(to_fetch, entries):
            forecast = _parse_daily(entry["daily"])
            cache_key = (round(lat, 2), round(lon, 2), forecast_days)
            _cache[cache_key] = (time.monotonic(), forecast)
            results[destination_id] = forecast
    except (httpx.HTTPError, KeyError, ValueError, IndexError):
        for destination_id, _, _ in to_fetch:
            results.setdefault(destination_id, None)

    return results


def _mode(values: list[int]) -> int:
    return Counter(values).most_common(1)[0][0]


_typical_cache: dict[tuple[float, float, int, int], tuple[float, DayForecast]] = {}


def get_typical_weather_for_dates(latitude: float, longitude: float, dates: list[date]) -> dict[str, DayForecast]:
    """Estimate "typical" weather for dates too far out for a real forecast
    (see get_weather_for_dates), by averaging actual recorded weather within
    a few days of the same calendar date across each of the last
    TYPICAL_LOOKBACK_YEARS years. This is a climatological estimate --
    "what this time of year usually looks like" -- not a prediction for the
    exact date, and every result comes back with is_estimate=True.

    Batched by design: fetches each lookback year's archive data once for
    the whole requested date span (plus a small buffer) rather than once
    per date, so a 14-day trip costs TYPICAL_LOOKBACK_YEARS archive calls
    total, not 14 * TYPICAL_LOOKBACK_YEARS. Never raises -- dates that can't
    be resolved are simply absent from the returned dict.
    """
    if not dates:
        return {}

    results: dict[str, DayForecast] = {}
    uncached: list[date] = []
    for target in dates:
        cache_key = (round(latitude, 2), round(longitude, 2), target.month, target.day)
        cached = _typical_cache.get(cache_key)
        if cached is not None and time.monotonic() - cached[0] < TYPICAL_CACHE_TTL_SECONDS:
            results[target.isoformat()] = cached[1]
        else:
            uncached.append(target)

    if not uncached:
        return results

    span_start = min(uncached)
    span_end = max(uncached)
    samples: dict[tuple[int, int], list[tuple[int, float, float, float]]] = {
        (d.month, d.day): [] for d in uncached
    }

    for years_back in range(1, TYPICAL_LOOKBACK_YEARS + 1):
        try:
            year_start = span_start.replace(year=span_start.year - years_back) - timedelta(days=2)
            year_end = span_end.replace(year=span_end.year - years_back) + timedelta(days=2)
        except ValueError:
            # Feb 29 anchor with no Feb 29 in this lookback year.
            year_start = date(span_start.year - years_back, span_start.month, min(span_start.day, 28)) - timedelta(
                days=2
            )
            year_end = date(span_end.year - years_back, span_end.month, min(span_end.day, 28)) + timedelta(days=2)

        try:
            response = httpx.get(
                ARCHIVE_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": year_start.isoformat(),
                    "end_date": year_end.isoformat(),
                    "daily": ARCHIVE_DAILY_FIELDS,
                    "timezone": "auto",
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            daily = response.json()["daily"]
            year_entries = list(
                zip(
                    daily["time"],
                    daily["weathercode"],
                    daily["temperature_2m_max"],
                    daily["temperature_2m_min"],
                    daily["precipitation_sum"],
                )
            )
        except (httpx.HTTPError, KeyError, ValueError):
            continue  # one bad lookback year shouldn't sink the whole estimate

        for date_str, code, temp_max, temp_min, precip in year_entries:
            if code is None or temp_max is None or temp_min is None:
                continue
            month_day = (int(date_str[5:7]), int(date_str[8:10]))
            if month_day in samples:
                samples[month_day].append((code, temp_max, temp_min, precip or 0.0))

    for target in uncached:
        entries = samples.get((target.month, target.day), [])
        if not entries:
            continue

        codes = [entry[0] for entry in entries]
        temp_maxes = [entry[1] for entry in entries]
        temp_mins = [entry[2] for entry in entries]
        wet_days = sum(1 for entry in entries if entry[3] >= 1.0)

        forecast = DayForecast(
            date=target.isoformat(),
            weather_code=_mode(codes),
            condition=_describe(_mode(codes)),
            temperature_max=round(sum(temp_maxes) / len(temp_maxes), 1),
            temperature_min=round(sum(temp_mins) / len(temp_mins), 1),
            precipitation_probability=round(100 * wet_days / len(entries), 1),
            is_estimate=True,
        )
        cache_key = (round(latitude, 2), round(longitude, 2), target.month, target.day)
        _typical_cache[cache_key] = (time.monotonic(), forecast)
        results[target.isoformat()] = forecast

    return results


def get_weather_for_dates(latitude: float, longitude: float, dates: list[date]) -> dict[str, DayForecast]:
    """Best-available weather for a list of calendar dates: a real Open-Meteo
    forecast for anything within the next 16 days, and a historical-average
    "typical weather" estimate (get_typical_weather_for_dates) for anything
    farther out -- which covers both trips planned months in advance and,
    as a graceful simplification, dates in the past. Never raises -- dates
    that can't be resolved by either path are simply absent from the
    returned dict, keyed by ISO date string.
    """
    if not dates:
        return {}

    today = date.today()
    near_term = [d for d in dates if 0 <= (d - today).days <= 16]
    far_term = [d for d in dates if d not in near_term]

    results: dict[str, DayForecast] = {}

    if near_term:
        max_days_out = max((d - today).days for d in near_term)
        try:
            forecast = get_forecast(latitude, longitude, max_days_out + 1)
            by_date = {day.date: day for day in forecast}
            for d in near_term:
                if d.isoformat() in by_date:
                    results[d.isoformat()] = by_date[d.isoformat()]
                else:
                    far_term.append(d)
        except WeatherUnavailableError:
            far_term.extend(near_term)

    if far_term:
        results.update(get_typical_weather_for_dates(latitude, longitude, far_term))

    return results
