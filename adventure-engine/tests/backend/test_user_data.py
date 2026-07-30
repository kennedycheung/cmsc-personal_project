"""Preferences and favorites -- the two per-user features that don't need
itinerary generation (and therefore don't need weather mocked). Saved
adventures (which do need itinerary generation) are covered in
test_recommendations_and_itineraries.py alongside the weather mocking setup.
"""


def test_preferences_lazily_created_then_updated(client, auth_headers):
    headers = auth_headers("pref.user@example.com", "hunter2222")

    fresh = client.get("/api/preferences/me", headers=headers)
    assert fresh.status_code == 200
    assert fresh.json() == {
        "max_budget_per_day": None,
        "interests": [],
        "travel_style": None,
        "updated_at": fresh.json()["updated_at"],
    }

    updated = client.put(
        "/api/preferences/me",
        headers=headers,
        json={"max_budget_per_day": 150, "interests": ["hiking", "food"], "travel_style": "Solo"},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["max_budget_per_day"] == 150
    assert body["interests"] == ["hiking", "food"]
    assert body["travel_style"] == "Solo"

    refetched = client.get("/api/preferences/me", headers=headers)
    assert refetched.json()["travel_style"] == "Solo"


def test_preferences_requires_auth(client):
    response = client.get("/api/preferences/me")
    assert response.status_code == 401


def test_favorites_add_list_idempotent_remove(client, auth_headers):
    headers = auth_headers("fav.user@example.com", "hunter2222")

    added = client.post("/api/favorites/", headers=headers, json={"destination_id": 1})
    assert added.status_code == 201
    assert added.json()["destination"]["name"] == "Banff National Park"

    added_again = client.post("/api/favorites/", headers=headers, json={"destination_id": 1})
    assert added_again.status_code == 201
    assert added_again.json()["id"] == added.json()["id"]

    listed = client.get("/api/favorites/", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    removed = client.delete("/api/favorites/1", headers=headers)
    assert removed.status_code == 204

    removed_again = client.delete("/api/favorites/1", headers=headers)
    assert removed_again.status_code == 204

    empty = client.get("/api/favorites/", headers=headers)
    assert empty.json() == []


def test_favorite_missing_destination_404(client, auth_headers):
    headers = auth_headers("fav.user2@example.com", "hunter2222")
    response = client.post("/api/favorites/", headers=headers, json={"destination_id": 9999})
    assert response.status_code == 404
