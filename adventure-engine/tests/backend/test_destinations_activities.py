def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_destinations_returns_seeded_data(client):
    response = client.get("/api/destinations/")
    assert response.status_code == 200
    destinations = response.json()
    assert len(destinations) == 14
    assert all("currency" in d and "latitude" in d for d in destinations)


def test_get_destination_by_id(client):
    response = client.get("/api/destinations/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Banff National Park"


def test_get_destination_404(client):
    response = client.get("/api/destinations/9999")
    assert response.status_code == 404


def test_search_destinations_by_region_and_budget(client):
    response = client.get(
        "/api/destinations/search", params={"region": "asia", "max_budget": 100, "interests": "food"}
    )
    assert response.status_code == 200
    names = {d["name"] for d in response.json()}
    assert names <= {"Chiang Mai", "Ho Chi Minh City", "Bali"}
    assert len(names) > 0


def test_search_destinations_rejects_inverted_budget_range(client):
    response = client.get("/api/destinations/search", params={"min_budget": 200, "max_budget": 100})
    assert response.status_code == 400


def test_list_activities_for_destination(client):
    response = client.get("/api/activities/destination/1")
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 4
    assert {a["name"] for a in activities} >= {"Lake Louise Canoe Tour", "Sulphur Mountain Gondola"}


def test_activities_for_missing_destination_404(client):
    response = client.get("/api/activities/destination/9999")
    assert response.status_code == 404
