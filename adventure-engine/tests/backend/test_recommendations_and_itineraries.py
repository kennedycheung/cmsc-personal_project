"""Recommendations, itineraries, and saved adventures all call out to
Open-Meteo internally. Real network calls would make this suite slow,
flaky, and rate-limit-prone in CI, so httpx.get is mocked here to return a
canned forecast -- see documentation/testing.md for the rationale (the
same graceful-degradation design that lets these endpoints survive a real
Open-Meteo outage is exactly what makes them straightforward to test this
way).
"""

from collections import Counter
from datetime import date, time, timedelta
from unittest.mock import patch

import pytest
from app.models.activity import Activity
from app.models.destination import Destination
from app.services import weather as weather_module
from app.services.itinerary import (
    DIVERSITY_PENALTY,
    NEIGHBORHOOD_BONUS,
    _day_cutoff_for,
    _score_activity,
    _score_time_fit,
    generate_itinerary,
)


def _make_activity(**overrides) -> Activity:
    defaults = dict(
        destination_id=1,
        name="Test Activity",
        category="museum",
        tags="museum,history,art",
        price=0.0,
        duration_hours=1.0,
        travel_minutes=10.0,
        is_outdoor=False,
        neighborhood=None,
        latitude=0.0,
        longitude=0.0,
    )
    defaults.update(overrides)
    return Activity(**defaults)


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


def test_recommendations_filtered_by_origin_distance(client):
    # Banff National Park's own coordinates as origin: a small radius should
    # only ever include Banff itself (and nothing 1000s of km away).
    response = client.get(
        "/api/recommendations/",
        params={"origin_lat": 51.4968, "origin_lon": -115.9281, "max_distance_km": 5, "top_n": 50},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert all(item["destination"]["name"] == "Banff National Park" for item in body)


def test_recommendations_without_origin_is_unfiltered(client):
    response = client.get("/api/recommendations/", params={"top_n": 50})
    assert response.status_code == 200
    assert len(response.json()) > 1


def test_recommendations_time_bucket_resolves_distance_server_side(client):
    # "half_day" resolves to a 15km radius -- from Banff's own coordinates,
    # that should behave identically to the explicit max_distance_km test.
    response = client.get(
        "/api/recommendations/",
        params={
            "origin_lat": 51.4968, "origin_lon": -115.9281,
            "time_bucket": "half_day", "top_n": 50,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert all(item["destination"]["name"] == "Banff National Park" for item in body)


def test_recommendations_stay_local_overrides_bucket_distance(client):
    # "two_weeks" alone is unconstrained, but "stay_local" scope forces a
    # tight radius regardless of how much time is available.
    response = client.get(
        "/api/recommendations/",
        params={
            "origin_lat": 51.4968, "origin_lon": -115.9281,
            "time_bucket": "two_weeks", "travel_scope": "stay_local", "top_n": 50,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert all(item["destination"]["name"] == "Banff National Park" for item in body)


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


def test_score_activity_multi_tag_partial_interest_match():
    activity = _make_activity(category="museum", tags="museum,history,art")
    common_args = dict(
        day_budget=None, max_travel_minutes=0, day_forecast=None, current_slot="afternoon",
        categories_today=Counter(), categories_trip=Counter(), neighborhoods_today=set(),
    )
    partial_match = _score_activity(activity, {"history", "architecture"}, **common_args)
    no_match = _score_activity(activity, {"architecture", "nightlife"}, **common_args)
    assert partial_match > no_match


def test_score_activity_diversity_penalty_reduces_repeat_score():
    activity = _make_activity(category="museum", tags="museum,history,art")
    common_args = dict(day_budget=None, max_travel_minutes=0, day_forecast=None, current_slot="afternoon")
    base_score = _score_activity(
        activity, set(), categories_today=Counter(), categories_trip=Counter(), neighborhoods_today=set(),
        **common_args,
    )
    repeated_score = _score_activity(
        activity, set(), categories_today=Counter({"museum": 2}), categories_trip=Counter(), neighborhoods_today=set(),
        **common_args,
    )
    assert repeated_score == pytest.approx(base_score * DIVERSITY_PENALTY**2)


def test_score_activity_neighborhood_bonus():
    activity = _make_activity(category="museum", tags="museum", neighborhood="Le Marais")
    common_args = dict(
        day_budget=None, max_travel_minutes=0, day_forecast=None, current_slot="afternoon",
        categories_today=Counter(), categories_trip=Counter(),
    )
    base_score = _score_activity(activity, set(), neighborhoods_today=set(), **common_args)
    bonus_score = _score_activity(activity, set(), neighborhoods_today={"Le Marais"}, **common_args)
    assert bonus_score == pytest.approx(base_score + NEIGHBORHOOD_BONUS)


def test_time_fit_prefers_matching_slot():
    assert _score_time_fit({"cafe"}, "morning") > _score_time_fit({"cafe"}, "evening")
    assert _score_time_fit({"nightlife"}, "late_night") > _score_time_fit({"nightlife"}, "morning")
    assert _score_time_fit({"some_untagged_category"}, "morning") == 0.6


def test_day_cutoff_extends_for_late_night_only_activities():
    assert _day_cutoff_for({"nightlife"}) == time(23, 59)
    assert _day_cutoff_for({"museum"}) == time(21, 0)
    assert _day_cutoff_for({"nightlife", "cafe"}) == time(21, 0)


def test_generate_itinerary_favors_diversity_over_repeats(db_session):
    destination = Destination(name="Test City", country="Testland", region="Test Region", latitude=0.0, longitude=0.0)
    db_session.add(destination)
    db_session.flush()

    activities = [
        Activity(
            destination_id=destination.id, name=f"Museum {i}", category="museum", tags="museum,history",
            price=0.0, duration_hours=1.0, travel_minutes=10.0, is_outdoor=False, latitude=0.0, longitude=0.0,
        )
        for i in range(3)
    ] + [
        Activity(
            destination_id=destination.id, name="City Park", category="park", tags="park,relaxation",
            price=0.0, duration_hours=1.0, travel_minutes=10.0, is_outdoor=False, latitude=0.0, longitude=0.0,
        )
    ]
    db_session.add_all(activities)
    db_session.commit()

    with patch.object(weather_module.httpx, "get", return_value=_FakeResponse(_fake_daily_payload())):
        result = generate_itinerary(db_session, destination.id, days=1)

    scheduled = result.days[0].activities
    assert len(scheduled) == 4
    # The 2nd pick should be the differently-categorized park, not a repeat
    # museum, since the diversity penalty makes the untouched category win
    # once the first museum has already been scheduled.
    assert scheduled[1].activity.category == "park"


def test_regenerate_day_excludes_locked_activities(db_session, client):
    destination = Destination(name="Test City 2", country="Testland", region="Test Region", latitude=1.0, longitude=1.0)
    db_session.add(destination)
    db_session.flush()

    kept = Activity(
        destination_id=destination.id, name="Keep Me", category="museum", tags="museum",
        price=0.0, duration_hours=1.0, travel_minutes=10.0, is_outdoor=False, latitude=1.0, longitude=1.0,
    )
    locked = Activity(
        destination_id=destination.id, name="Already Used Elsewhere", category="park", tags="park",
        price=0.0, duration_hours=1.0, travel_minutes=10.0, is_outdoor=False, latitude=1.0, longitude=1.0,
    )
    db_session.add_all([kept, locked])
    db_session.commit()

    response = client.post(
        f"/api/itineraries/{destination.id}/regenerate-day",
        json={"day": 1, "days": 1, "locked_activity_ids": [locked.id]},
    )
    assert response.status_code == 200
    body = response.json()
    names = {item["activity"]["name"] for item in body["activities"]}
    assert "Already Used Elsewhere" not in names
    assert "Keep Me" in names


def test_regenerate_day_missing_destination_404(client):
    response = client.post(
        "/api/itineraries/9999/regenerate-day", json={"day": 1, "days": 1, "locked_activity_ids": []}
    )
    assert response.status_code == 404


def test_activity_alternatives_ranked_by_tag_overlap(db_session, client):
    destination = Destination(name="Test City 3", country="Testland", region="Test Region", latitude=2.0, longitude=2.0)
    db_session.add(destination)
    db_session.flush()

    target = Activity(
        destination_id=destination.id, name="Target Museum", category="museum", tags="museum,history,art",
        price=0.0, duration_hours=1.0, travel_minutes=10.0, is_outdoor=False, latitude=2.0, longitude=2.0,
    )
    close_match = Activity(
        destination_id=destination.id, name="History Gallery", category="gallery", tags="gallery,history,art",
        price=0.0, duration_hours=1.0, travel_minutes=10.0, is_outdoor=False, latitude=2.0, longitude=2.0,
    )
    unrelated = Activity(
        destination_id=destination.id, name="Nightclub", category="nightlife", tags="nightlife,bar",
        price=0.0, duration_hours=1.0, travel_minutes=10.0, is_outdoor=False, latitude=2.0, longitude=2.0,
    )
    db_session.add_all([target, close_match, unrelated])
    db_session.commit()

    response = client.get(f"/api/activities/{target.id}/alternatives")
    assert response.status_code == 200
    body = response.json()
    names = [item["name"] for item in body]
    assert names[0] == "History Gallery"
    assert "Target Museum" not in names


def test_activity_alternatives_missing_activity_404(client):
    response = client.get("/api/activities/9999/alternatives")
    assert response.status_code == 404


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
