"""Currency arbitrage.

RelativeStrength = BaselineRate / CurrentRate
AdjustedBudgetPerDay = destination.budget_per_day * RelativeStrength
Savings = destination.budget_per_day - AdjustedBudgetPerDay
ArbitragePercent = (1 - RelativeStrength) * 100

Uses Frankfurter (https://www.frankfurter.app), a free ECB-backed exchange
rate API -- no key required, same "use a real free API when one exists"
principle as Open-Meteo (weather) and OSRM (walking routes) elsewhere in
this app. See documentation/backpacker_optimizations.md for the full
derivation, worked example, and currency-coverage caveats.
"""

import time
from dataclasses import dataclass
from datetime import date, timedelta

import httpx

FRANKFURTER_BASE_URL = "https://api.frankfurter.app"
REQUEST_TIMEOUT_SECONDS = 5.0
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours; Frankfurter's ECB data updates once daily anyway.
BASELINE_DAYS_AGO = 365

_cache: dict[tuple[str, str, str], tuple[float, dict[str, float]]] = {}


class CurrencyRateUnavailableError(Exception):
    """Raised when a currency isn't covered by Frankfurter or the API can't be reached."""


def _fetch_rates(base_currency: str, target_currencies: list[str], as_of: str) -> dict[str, float]:
    """as_of is 'latest' or an ISO date string. Returns {currency: rate} for
    whichever of the requested currencies Frankfurter actually covers -- an
    unsupported currency is silently omitted from the response, not an
    error, so callers must check membership rather than assume every
    requested currency comes back."""
    cache_key = (base_currency, ",".join(sorted(target_currencies)), as_of)
    cached = _cache.get(cache_key)
    if cached is not None and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    try:
        response = httpx.get(
            f"{FRANKFURTER_BASE_URL}/{as_of}",
            params={"from": base_currency, "to": ",".join(target_currencies)},
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        response.raise_for_status()
        rates = response.json()["rates"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise CurrencyRateUnavailableError(str(exc)) from exc

    _cache[cache_key] = (time.monotonic(), rates)
    return rates


@dataclass
class CurrencyArbitrageResult:
    local_currency: str
    current_rate: float
    baseline_rate: float
    relative_strength: float
    adjusted_budget_per_day: float
    savings: float
    arbitrage_percent: float


def _compute(
    budget_per_day: float, local_currency: str, current_rate: float, baseline_rate: float
) -> CurrencyArbitrageResult:
    relative_strength = baseline_rate / current_rate
    adjusted_budget = budget_per_day * relative_strength
    return CurrencyArbitrageResult(
        local_currency=local_currency,
        current_rate=current_rate,
        baseline_rate=baseline_rate,
        relative_strength=round(relative_strength, 4),
        adjusted_budget_per_day=round(adjusted_budget, 2),
        savings=round(budget_per_day - adjusted_budget, 2),
        arbitrage_percent=round((1 - relative_strength) * 100, 2),
    )


def evaluate_currency_arbitrage(
    budget_per_day: float, local_currency: str, home_currency: str = "USD"
) -> CurrencyArbitrageResult:
    """Raises CurrencyRateUnavailableError if the currency isn't covered by
    Frankfurter or the API can't be reached."""
    if local_currency == home_currency:
        return _compute(budget_per_day, local_currency, 1.0, 1.0)

    baseline_date = (date.today() - timedelta(days=BASELINE_DAYS_AGO)).isoformat()
    current_rates = _fetch_rates(home_currency, [local_currency], "latest")
    baseline_rates = _fetch_rates(home_currency, [local_currency], baseline_date)

    if local_currency not in current_rates or local_currency not in baseline_rates:
        raise CurrencyRateUnavailableError(f"{local_currency} is not covered by Frankfurter")

    return _compute(budget_per_day, local_currency, current_rates[local_currency], baseline_rates[local_currency])


def evaluate_currency_arbitrage_batch(
    destinations: list[tuple[int, float, str]], home_currency: str = "USD"
) -> dict[int, CurrencyArbitrageResult | None]:
    """destinations: (destination_id, budget_per_day, local_currency) triples.

    One request for "latest" and one for the baseline date cover every
    destination at once (Frankfurter accepts a comma-separated `to` list),
    regardless of how many destinations are passed in -- the same batching
    lesson learned from the weather integration (see weather_integration.md)
    applies here too. Returns id -> result, or id -> None if that currency
    is unavailable. Never raises.
    """
    results: dict[int, CurrencyArbitrageResult | None] = {}

    to_fetch = [(did, budget, cur) for did, budget, cur in destinations if cur != home_currency]
    for did, budget, cur in destinations:
        if cur == home_currency:
            results[did] = _compute(budget, cur, 1.0, 1.0)

    if not to_fetch:
        return results

    target_currencies = sorted({cur for _, _, cur in to_fetch})
    baseline_date = (date.today() - timedelta(days=BASELINE_DAYS_AGO)).isoformat()

    try:
        current_rates = _fetch_rates(home_currency, target_currencies, "latest")
        baseline_rates = _fetch_rates(home_currency, target_currencies, baseline_date)
    except CurrencyRateUnavailableError:
        current_rates, baseline_rates = {}, {}

    for did, budget, cur in to_fetch:
        if cur in current_rates and cur in baseline_rates:
            results[did] = _compute(budget, cur, current_rates[cur], baseline_rates[cur])
        else:
            results[did] = None

    return results
