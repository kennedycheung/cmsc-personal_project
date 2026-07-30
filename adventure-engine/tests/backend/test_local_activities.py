"""Local-activity discovery hits the same real Overpass instance as OSM
ingestion, so httpx.post is mocked the same way -- see test_osm_activities.py."""

from unittest.mock import patch

import pytest

from app.services import osm_activities as osm_module


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def _fake_overpass_payload() -> dict:
    return {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "lat": 41.880,
                "lon": -87.625,
                "tags": {"amenity": "cafe", "name": "Fake Cafe"},
            },
            {
                "type": "node",
                "id": 2,
                "lat": 41.881,
                "lon": -87.626,
                "tags": {"tourism": "museum", "name": "Fake Museum"},
            },
            # A way result -- has no top-level lat/lon, only a computed "center".
            {
                "type": "way",
                "id": 3,
                "center": {"lat": 41.882, "lon": -87.627},
                "tags": {"leisure": "park", "name": "Fake Park"},
            },
            # No name -- should be silently dropped, not crash.
            {"type": "node", "id": 4, "lat": 41.883, "lon": -87.628, "tags": {"amenity": "cafe"}},
        ]
    }


@pytest.fixture(autouse=True)
def _mock_overpass():
    with patch.object(osm_module.httpx, "post", return_value=_FakeResponse(_fake_overpass_payload())):
        yield


def test_discover_local_activities_groups_by_category():
    from app.services.local_activities import discover_local_activities

    grouped = discover_local_activities(41.8781, -87.6298, "Chicago")

    assert any(a.name == "Fake Cafe" for a in grouped["food"])
    assert any(a.name == "Fake Museum" for a in grouped["culture"])
    # Way results (no top-level lat/lon) still resolve via "center".
    assert any(a.name == "Fake Park" for a in grouped["relaxation"])
    # Every returned activity carries a real distance from the origin.
    assert all(a.distance_km >= 0 for activities in grouped.values() for a in activities)


def test_discover_local_activities_respects_group_filter():
    from app.services.local_activities import discover_local_activities

    grouped = discover_local_activities(41.8781, -87.6298, "Chicago", groups=["food"])

    assert set(grouped.keys()) == {"food"}
    assert any(a.name == "Fake Cafe" for a in grouped["food"])


def test_local_activities_endpoint(client):
    response = client.get(
        "/api/local-activities/",
        params={"latitude": 41.8781, "longitude": -87.6298, "origin_label": "Chicago", "groups": "food,culture"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body["groups"].keys()) == {"food", "culture"}
    assert any(a["name"] == "Fake Cafe" for a in body["groups"]["food"])


def test_local_activities_endpoint_upstream_failure(client):
    import httpx

    with patch.object(osm_module.httpx, "post", side_effect=httpx.ConnectError("boom")):
        response = client.get(
            "/api/local-activities/", params={"latitude": 41.8781, "longitude": -87.6298}
        )
    assert response.status_code == 502
