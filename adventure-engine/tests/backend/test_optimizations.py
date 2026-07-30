"""Backpacker optimization endpoints. Five of the six calculators are pure
local math (no network) and are tested directly against the seeded data --
these double as regression tests for the worked examples in
documentation/backpacker_optimizations.md. Currency arbitrage is the one
real live-API integration (Frankfurter), so httpx.get is mocked here the
same way Open-Meteo is mocked elsewhere.
"""

from unittest.mock import patch

import pytest

from app.services.optimizations import currency as currency_module


def test_airport_optimization_recommends_farther_cheaper_airport_for_kyoto(client):
    response = client.get("/api/optimizations/airports/6")
    assert response.status_code == 200
    body = response.json()
    assert body["recommended"]["iata_code"] == "NGO"
    assert body["primary"]["iata_code"] == "KIX"
    assert body["savings_vs_primary"] == pytest.approx(75.0, abs=0.5)


def test_airport_optimization_404_when_no_data(client):
    # Lisbon has no modeled alternate airports.
    response = client.get("/api/optimizations/airports/2")
    assert response.status_code == 404


def test_overnight_transport_savings_for_chiang_mai(client):
    response = client.get(
        "/api/optimizations/overnight-transport/4", params={"overnight_price": 25, "daytime_price": 15}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["lodging_per_night"] == pytest.approx(28.0)
    assert body["net_savings"] == pytest.approx(18.0)
    assert body["worth_it"] is True


def test_open_jaw_realistic_pair_reports_savings_and_time(client):
    response = client.get(
        "/api/optimizations/open-jaw",
        params={
            "entry_destination_id": 4,  # Chiang Mai
            "exit_destination_id": 14,  # Ho Chi Minh City
            "round_trip_fare": 900,
            "one_way_fare_out": 500,
            "one_way_fare_back": 480,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["unrealistic_overland_distance"] is False
    assert body["backtrack_time_hours"] > 0
    assert body["net_savings"] == pytest.approx(5.17, abs=1.0)


def test_open_jaw_flags_unrealistic_overland_distance(client):
    response = client.get(
        "/api/optimizations/open-jaw",
        params={"entry_destination_id": 13, "exit_destination_id": 6},  # Cape Town <-> Kyoto
    )
    assert response.status_code == 200
    assert response.json()["unrealistic_overland_distance"] is True


def test_positioning_trip_through_reykjavik(client):
    response = client.get(
        "/api/optimizations/positioning",
        params={
            "hub_destination_id": 7,  # Reykjavik
            "direct_itinerary_cost": 700,
            "fare_home_to_hub": 300,
            "fare_hub_to_final": 180,
            "extra_nights": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["layover_lodging_cost"] == pytest.approx(96.0)
    assert body["net_savings"] == pytest.approx(124.0)
    assert body["worth_it"] is True


def test_seasonal_arbitrage_reykjavik_best_and_peak_month(client):
    response = client.get("/api/optimizations/seasonal/7", params={"month": 7})
    assert response.status_code == 200
    body = response.json()
    assert body["best_month"]["month_name"] == "April"
    assert body["peak_month"]["month_name"] == "July"
    assert body["savings_vs_peak"] == pytest.approx(132.0)


def test_seasonal_arbitrage_rejects_invalid_month(client):
    response = client.get("/api/optimizations/seasonal/7", params={"month": 13})
    assert response.status_code == 422


class _FakeRatesResponse:
    def __init__(self, rates: dict[str, float]):
        self._rates = rates

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"rates": self._rates}


@pytest.fixture()
def _mock_currency_rates():
    currency_module._cache.clear()

    def _apply(current_rate: float, baseline_rate: float, currency_code: str = "JPY"):
        responses = [_FakeRatesResponse({currency_code: current_rate}), _FakeRatesResponse({currency_code: baseline_rate})]
        return patch.object(currency_module.httpx, "get", side_effect=responses)

    yield _apply
    currency_module._cache.clear()


def test_currency_arbitrage_favorable_when_local_currency_weakened(client, _mock_currency_rates):
    with _mock_currency_rates(current_rate=163.68, baseline_rate=148.77, currency_code="JPY"):
        response = client.get("/api/optimizations/currency/6")  # Kyoto, JPY
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["arbitrage_percent"] == pytest.approx(9.11, abs=0.1)
    assert body["savings"] > 0


def test_currency_arbitrage_unavailable_for_unsupported_currency(client):
    currency_module._cache.clear()
    with patch.object(currency_module.httpx, "get", return_value=_FakeRatesResponse({})):
        response = client.get("/api/optimizations/currency/8")  # Marrakech, MAD (not covered by Frankfurter)
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["arbitrage_percent"] is None
    currency_module._cache.clear()


def test_currency_arbitrage_same_currency_as_home_needs_no_api_call(client):
    currency_module._cache.clear()
    with patch.object(currency_module.httpx, "get") as mocked_get:
        response = client.get("/api/optimizations/currency/3", params={"home_currency": "USD"})  # Sedona, USD
    mocked_get.assert_not_called()
    assert response.status_code == 200
    assert response.json()["arbitrage_percent"] == 0.0
