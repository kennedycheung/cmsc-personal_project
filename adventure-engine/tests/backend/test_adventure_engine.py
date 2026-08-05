"""The adventure recommendation engine builds on local_activities.py (which
already hits real Overpass, mocked the same way as test_local_activities.py)
plus weather.py (mocked the same way as everywhere else in this suite).
Clustering/scoring/itinerary are pure functions tested directly against
constructed LocalActivity fixtures, no network involved.
"""

from unittest.mock import patch

import pytest
from app.services import osm_activities as osm_module
from app.services import weather as weather_module
from app.services.adventure_engine.clustering import cluster_activities
from app.services.adventure_engine.engine import recommend_adventures
from app.services.adventure_engine.itinerary import build_itinerary
from app.services.adventure_engine.providers import PROVIDERS, ProviderUnavailableError
from app.services.adventure_engine.reasoning import build_summary
from app.services.adventure_engine.scoring import score_cluster
from app.services.adventure_engine.types import AdventureRequest
from app.services.local_activities import LocalActivity


def _make_activity(**overrides) -> LocalActivity:
    defaults = dict(
        name="Test Activity",
        description="A nice place",
        group="culture",
        category="museum",
        location="123 Main St",
        latitude=41.880,
        longitude=-87.625,
        distance_km=1.0,
        duration_hours=1.5,
        is_outdoor=False,
        opening_time="09:00",
        closing_time="17:00",
    )
    defaults.update(overrides)
    return LocalActivity(**defaults)


def _sample_request() -> AdventureRequest:
    return AdventureRequest(latitude=41.878, longitude=-87.629, location_label="Chicago")


# --- clustering --------------------------------------------------------------


def test_cluster_activities_groups_nearby_activities_together():
    activities = [
        _make_activity(name="Museum", latitude=41.880, longitude=-87.625),
        _make_activity(name="Cafe", group="food", category="cafe", latitude=41.8805, longitude=-87.6255),
        _make_activity(name="Far Park", group="nature", category="park", latitude=42.500, longitude=-88.500),
    ]

    clusters = cluster_activities(activities)

    assert len(clusters) == 2
    sizes = sorted(len(c.activities) for c in clusters)
    assert sizes == [1, 2]


def test_cluster_activities_keeps_singletons_not_dropped():
    activities = [_make_activity(name="Solo Landmark")]
    clusters = cluster_activities(activities)
    assert len(clusters) == 1
    assert len(clusters[0].activities) == 1


# --- scoring -------------------------------------------------------------------


def test_score_cluster_rewards_interest_match():
    request_matching = AdventureRequest(latitude=41.878, longitude=-87.629, location_label="Chicago", interests=["museum"])
    request_no_match = AdventureRequest(
        latitude=41.878, longitude=-87.629, location_label="Chicago", interests=["nightlife"]
    )
    cluster = cluster_activities([_make_activity(category="museum", group="culture")])[0]

    score_match, _confidence, _reasons = score_cluster(cluster, request_matching)
    score_no_match, _confidence2, _reasons2 = score_cluster(cluster, request_no_match)

    assert score_match > score_no_match


def test_score_cluster_budget_fit_is_neutral_and_says_so():
    request = _sample_request()
    cluster = cluster_activities([_make_activity()])[0]
    _total, _confidence, reasons = score_cluster(cluster, request)

    budget_reason = next(r for r in reasons if r.factor == "budget_fit")
    assert budget_reason.score == 0.5
    assert "OpenStreetMap" in budget_reason.reason


def test_score_cluster_confidence_reflects_data_completeness():
    request = _sample_request()
    complete = cluster_activities(
        [_make_activity(description="Detailed", opening_time="09:00", closing_time="17:00", location="Real address")]
    )[0]
    sparse = cluster_activities(
        [_make_activity(description=None, opening_time=None, closing_time=None, location="")]
    )[0]

    _s1, confidence_complete, _r1 = score_cluster(complete, request)
    _s2, confidence_sparse, _r2 = score_cluster(sparse, request)

    assert confidence_complete > confidence_sparse


def test_score_cluster_density_prefers_larger_clusters():
    request = _sample_request()
    small = cluster_activities([_make_activity(name="A")])[0]
    large_activities = [_make_activity(name=f"Stop {i}", latitude=41.880 + i * 0.001) for i in range(5)]
    large = cluster_activities(large_activities)[0]

    score_small, _c1, _r1 = score_cluster(small, request)
    score_large, _c2, _r2 = score_cluster(large, request)

    assert score_large > score_small


# --- reasoning -----------------------------------------------------------------


def test_build_summary_includes_top_reasons_and_location():
    request = _sample_request()
    cluster = cluster_activities([_make_activity()])[0]
    _total, _confidence, reasons = score_cluster(cluster, request)

    summary = build_summary(reasons, "Chicago")

    assert summary.startswith("Chicago:")
    assert len(summary) > len("Chicago: .")


# --- itinerary -------------------------------------------------------------------


def test_build_itinerary_assigns_named_slots_and_walking_time():
    activities = [
        _make_activity(name="Morning Cafe", group="food", category="cafe", latitude=41.880, longitude=-87.625),
        _make_activity(name="Museum Visit", group="culture", category="museum", latitude=41.881, longitude=-87.626),
        _make_activity(
            name="Dinner Spot", group="food", category="restaurant", latitude=41.882, longitude=-87.627
        ),
    ]
    cluster = cluster_activities(activities)[0]

    itinerary = build_itinerary(cluster)

    assert len(itinerary.slots) == 3
    slot_names = [s.slot for s in itinerary.slots]
    assert "morning" in slot_names  # cafe should land in the morning slot
    # First stop has no "previous", so no walking time; later stops do.
    assert itinerary.slots[0].walking_minutes_from_previous is None
    assert all(s.walking_minutes_from_previous is not None for s in itinerary.slots[1:])
    assert itinerary.total_walking_minutes > 0


def test_build_itinerary_never_force_fits_a_mismatched_activity_into_a_slot():
    # Only a theater (an "evening" fit) and a bookstore (an "afternoon"
    # fit) -- neither belongs at breakfast/lunch, so those slots should be
    # skipped rather than force-filled, and nothing should land in the
    # wrong slot just because it happened to still be in the pool.
    activities = [
        _make_activity(name="Storefront Theater", group="entertainment", category="theater"),
        _make_activity(name="Barnes & Noble", group="shopping", category="bookstore"),
    ]
    cluster = cluster_activities(activities)[0]

    itinerary = build_itinerary(cluster)

    slot_names = [s.slot for s in itinerary.slots]
    assert "lunch" not in slot_names
    assert "morning" not in slot_names
    assigned_names = {s.activity.name for s in itinerary.slots}
    assert assigned_names == {"Storefront Theater", "Barnes & Noble"}
    assert itinerary.optional_activities == []


def test_build_itinerary_single_activity_has_no_walking_time():
    cluster = cluster_activities([_make_activity()])[0]
    itinerary = build_itinerary(cluster)
    assert len(itinerary.slots) == 1
    assert itinerary.slots[0].walking_minutes_from_previous is None
    assert itinerary.total_walking_minutes == 0


# --- providers -------------------------------------------------------------------


def test_all_placeholder_providers_raise_unavailable():
    assert set(PROVIDERS.keys()) == {"flights", "hotels", "transit", "events", "restaurants"}
    with pytest.raises(ProviderUnavailableError):
        PROVIDERS["flights"].search_flights("ORD", "NRT", "2026-09-01")
    with pytest.raises(ProviderUnavailableError):
        PROVIDERS["hotels"].search_hotels(41.0, -87.0, "2026-09-01", "2026-09-03")
    with pytest.raises(ProviderUnavailableError):
        PROVIDERS["transit"].get_routes(41.0, -87.0, 41.1, -87.1)
    with pytest.raises(ProviderUnavailableError):
        PROVIDERS["events"].search_events(41.0, -87.0, "2026-09-01")
    with pytest.raises(ProviderUnavailableError):
        PROVIDERS["restaurants"].search_restaurants(41.0, -87.0)


# --- full engine / endpoint --------------------------------------------------------


def _fake_overpass_payload() -> dict:
    return {
        "elements": [
            {"type": "node", "id": 1, "lat": 41.880, "lon": -87.625, "tags": {"amenity": "cafe", "name": "Real Cafe"}},
            {
                "type": "node",
                "id": 2,
                "lat": 41.8805,
                "lon": -87.6255,
                "tags": {"tourism": "museum", "name": "Real Museum"},
            },
            {
                "type": "node",
                "id": 3,
                "lat": 42.5,
                "lon": -88.5,
                "tags": {"leisure": "park", "name": "Distant Park"},
            },
        ]
    }


@pytest.fixture(autouse=True)
def _mock_overpass():
    with patch.object(osm_module.httpx, "post", return_value=_FakeOverpassResponse()):
        yield


class _FakeOverpassResponse:
    def __init__(self):
        self.status_code = 200
        self.headers: dict = {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return _fake_overpass_payload()


class _FakeWeatherResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "daily": {
                "time": ["2026-08-05"],
                "weathercode": [1],
                "temperature_2m_max": [22.0],
                "temperature_2m_min": [12.0],
                "precipitation_probability_max": [5],
            }
        }


def test_recommend_adventures_returns_ranked_clusters_with_reasoning():
    weather_module._cache.clear()
    with patch.object(weather_module.httpx, "get", return_value=_FakeWeatherResponse()):
        request = AdventureRequest(latitude=41.878, longitude=-87.629, location_label="Chicago")
        recommendations, warnings = recommend_adventures(request)

    assert warnings == []
    assert len(recommendations) >= 1
    top = recommendations[0]
    assert top.summary.startswith("Chicago:")
    assert len(top.reasons) == 8  # one per registered scoring factor
    assert all(r.reason for r in top.reasons)  # every factor has real explanatory text
    scores = [r.total_score for r in recommendations]
    assert scores == sorted(scores, reverse=True)


def test_recommend_endpoint_full_pipeline(client):
    weather_module._cache.clear()
    with patch.object(weather_module.httpx, "get", return_value=_FakeWeatherResponse()):
        response = client.post(
            "/api/adventures/recommend",
            json={"latitude": 41.878, "longitude": -87.629, "location_label": "Chicago", "interests": ["museum"]},
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["recommendations"]) >= 1
    first = body["recommendations"][0]
    assert "summary" in first and first["summary"]
    assert len(first["reasons"]) == 8
