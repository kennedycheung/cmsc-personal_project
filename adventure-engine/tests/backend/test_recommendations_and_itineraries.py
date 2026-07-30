"""Recommendations, itineraries, and saved adventures all call out to
Open-Meteo internally. Real network calls would make this suite slow,
flaky, and rate-limit-prone in CI, so httpx.get is mocked here to return a
canned forecast -- see documentation/testing.md for the rationale (the
same graceful-degradation design that lets these endpoints survive a real
Open-Meteo outage is exactly what makes them straightforward to test this
way).
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from app.services import weather as weather_module


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def _fake_daily_payload(days: int = 14) -> dict:
    # Dates start from today, matching what a real Open-Meteo forecast call
    # (always relative to "now") would return -- a fixed hardcoded date range
    # would silently stop matching real date-based lookups once "today"
    # moves past it.
    today = date.today()
    return {
        "daily": {
            "time": [(today + timedelta(days=offset)).isoformat() for offset in range(days)],
            "weathercode": [1] * days,
            "temperature_2m_max": [20.0] * days,
            "temperature_2m_min": [10.0] * days,
            "precipitation_probability_max": [10] * days,
        }
    }


def _fake_archive_payload() -> dict:
    # A full fake year (fixed reference year, values constant) so the
    # get_typical_weather_for_dates aggregation finds a (month, day) match
    # regardless of which future date a test asks about.
    import datetime as _dt

    start = _dt.date(2019, 1, 1)
    days = [start + _dt.timedelta(days=i) for i in range(365)]
    return {
        "daily": {
            "time": [d.isoformat() for d in days],
            "weathercode": [1] * len(days),
            "temperature_2m_max": [22.0] * len(days),
            "temperature_2m_min": [12.0] * len(days),
            "precipitation_sum": [0.5] * len(days),
        }
    }


@pytest.fixture(autouse=True)
def _mock_weather_and_clear_cache():
    weather_module._cache.clear()
    with patch.object(weather_module.httpx, "get", return_value=_FakeResponse(_fake_daily_payload())):
        yield
    weather_module._cache.clear()


def test_recommendations_returns_ranked_destinations(client):
    response = client.get("/api/recommendations/", params={"max_budget": 150, "interests": "hiking,scenery"})
    assert response.status_code == 200
    body = response.json()
    assert 1 <= len(body) <= 10
    scores = [item["adventure_score"] for item in body]
    assert scores == sorted(scores, reverse=True)
    assert "weather" in body[0]["score_breakdown"]


def test_itinerary_generation_for_banff(client):
    response = client.get("/api/itineraries/1", params={"days": 2, "interests": "hiking,relaxation"})
    assert response.status_code == 200
    body = response.json()
    assert body["destination"]["name"] == "Banff National Park"
    assert len(body["days"]) == 2
    assert body["days"][0]["weather"]["condition"]


def test_itinerary_missing_destination_404(client):
    response = client.get("/api/itineraries/9999", params={"days": 2})
    assert response.status_code == 404


def test_itinerary_with_near_term_start_date_uses_real_forecast(client):
    near_date = (date.today() + timedelta(days=5)).isoformat()
    response = client.get("/api/itineraries/1", params={"days": 2, "start_date": near_date})
    assert response.status_code == 200
    body = response.json()
    assert body["days"][0]["weather"]["date"] == near_date
    assert body["days"][0]["weather"]["is_estimate"] is False


def test_itinerary_with_far_future_start_date_uses_typical_estimate(client):
    weather_module._cache.clear()
    weather_module._typical_cache.clear()
    far_date = date.today() + timedelta(days=200)

    def _fake_get(url, params=None, timeout=None):
        if url == weather_module.ARCHIVE_URL:
            return _FakeResponse(_fake_archive_payload())
        return _FakeResponse(_fake_daily_payload())

    with patch.object(weather_module.httpx, "get", side_effect=_fake_get):
        response = client.get("/api/itineraries/1", params={"days": 2, "start_date": far_date.isoformat()})

    assert response.status_code == 200
    body = response.json()
    assert body["days"][0]["weather"]["is_estimate"] is True
    assert any("historical-average estimate" in w for w in body["warnings"])
    weather_module._typical_cache.clear()


def test_saved_adventure_lifecycle_and_cross_user_isolation(client, auth_headers):
    owner_headers = auth_headers("owner@example.com", "hunter2222")
    other_headers = auth_headers("other@example.com", "hunter2222")

    created = client.post(
        "/api/saved-adventures/",
        headers=owner_headers,
        json={"destination_id": 1, "name": "Banff Getaway", "days": 2, "budget": 300, "interests": ["hiking"]},
    )
    assert created.status_code == 201
    saved = created.json()
    assert saved["name"] == "Banff Getaway"
    assert len(saved["itinerary"]["days"]) == 2
    saved_id = saved["id"]

    listed = client.get("/api/saved-adventures/", headers=owner_headers)
    assert len(listed.json()) == 1

    other_view = client.get(f"/api/saved-adventures/{saved_id}", headers=other_headers)
    assert other_view.status_code == 404

    other_delete = client.delete(f"/api/saved-adventures/{saved_id}", headers=other_headers)
    assert other_delete.status_code == 404

    owner_delete = client.delete(f"/api/saved-adventures/{saved_id}", headers=owner_headers)
    assert owner_delete.status_code == 204

    gone = client.get(f"/api/saved-adventures/{saved_id}", headers=owner_headers)
    assert gone.status_code == 404
