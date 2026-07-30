"""Geocoding hits a real public Nominatim instance, so httpx.get is mocked
here the same way it's mocked for weather -- see documentation/testing.md."""

from unittest.mock import patch

import pytest

from app.services import geocoding as geocoding_module


class _FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self):
        return self._payload


def _fake_result():
    return [
        {
            "lat": "41.8755616",
            "lon": "-87.6244212",
            "display_name": "Chicago, Cook County, Illinois, United States",
            "address": {"country": "United States"},
        }
    ]


@pytest.fixture(autouse=True)
def _reset_geocoding_state():
    geocoding_module._cache.clear()
    geocoding_module._last_request_at = 0.0
    yield
    geocoding_module._cache.clear()


def test_geocode_resolves_known_query():
    with patch.object(geocoding_module.httpx, "get", return_value=_FakeResponse(_fake_result())):
        result = geocoding_module.geocode("Chicago")

    assert result.latitude == pytest.approx(41.8755616)
    assert result.longitude == pytest.approx(-87.6244212)
    assert result.country == "United States"


def test_geocode_raises_on_no_results():
    with patch.object(geocoding_module.httpx, "get", return_value=_FakeResponse([])):
        with pytest.raises(geocoding_module.GeocodeError):
            geocoding_module.geocode("nonexistentplacezzz")


def test_geocode_endpoint_returns_location(client):
    with patch.object(geocoding_module.httpx, "get", return_value=_FakeResponse(_fake_result())):
        response = client.get("/api/geocode/", params={"query": "Chicago"})

    assert response.status_code == 200
    body = response.json()
    assert body["label"].startswith("Chicago")
    assert body["country"] == "United States"


def test_geocode_endpoint_404_when_not_found(client):
    with patch.object(geocoding_module.httpx, "get", return_value=_FakeResponse([])):
        response = client.get("/api/geocode/", params={"query": "nonexistentplacezzz"})

    assert response.status_code == 404
