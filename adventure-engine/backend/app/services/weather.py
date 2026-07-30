"""Open-Meteo forecast client: free, no API key, used to weight itinerary
scheduling and recommendation scoring by forecasted weather.

See documentation/weather_integration.md for the endpoint shape, the WMO
weather-code mapping, and the good/bad weather thresholds used elsewhere.
"""

import time
from dataclasses import dataclass

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 5.0
CACHE_TTL_SECONDS = 1800  # 30 minutes -- forecasts don't meaningfully change faster than this.
DAILY_FIELDS = "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max"

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
