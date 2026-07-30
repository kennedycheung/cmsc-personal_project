"""OSM ingestion hits a real public Overpass instance, so httpx.post is
mocked here the same way httpx.get is mocked for weather/deals -- see
documentation/testing.md for the rationale."""

from unittest.mock import patch

import pytest
from app.services import osm_activities as osm_module


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self) -> dict:
        return self._payload


def _fake_overpass_payload() -> dict:
    return {
        "elements": [
            {
                "type": "node",
                "id": 111,
                "lat": 48.858,
                "lon": 2.294,
                "tags": {"tourism": "museum", "name": "Fake Museum", "opening_hours": "09:00-18:00"},
            },
            {
                "type": "node",
                "id": 222,
                "lat": 48.860,
                "lon": 2.300,
                "tags": {"leisure": "park", "name": "Fake Park"},
            },
            # No name -- should be skipped, not crash.
            {"type": "node", "id": 333, "lat": 48.861, "lon": 2.301, "tags": {"tourism": "viewpoint"}},
        ]
    }


@pytest.fixture(autouse=True)
def _mock_overpass():
    with patch.object(osm_module.httpx, "post", return_value=_FakeResponse(_fake_overpass_payload())):
        yield


def test_ingest_osm_activities_for_one_destination(client):
    before = client.get("/api/activities/destination/1").json()

    response = client.post("/api/activities/ingest-osm", params={"destination_id": 1})
    assert response.status_code == 200
    summary = response.json()
    assert summary["inserted"] == 2
    assert summary["skipped_unnamed"] == 1
    assert summary["errors"] == []

    after = client.get("/api/activities/destination/1").json()
    assert len(after) == len(before) + 2
    osm_names = {a["name"] for a in after if a["source"] == "osm"}
    assert osm_names == {"Fake Museum", "Fake Park"}


def test_reingesting_osm_activities_is_idempotent(client):
    first = client.post("/api/activities/ingest-osm", params={"destination_id": 1}).json()
    assert first["inserted"] == 2

    second = client.post("/api/activities/ingest-osm", params={"destination_id": 1}).json()
    assert second["inserted"] == 0
    assert second["updated"] == 2

    activities = client.get("/api/activities/destination/1").json()
    assert sum(1 for a in activities if a["source"] == "osm") == 2


def test_ingest_osm_activities_missing_destination_404(client):
    response = client.post("/api/activities/ingest-osm", params={"destination_id": 9999})
    assert response.status_code == 404
