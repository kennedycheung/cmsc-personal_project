def test_deals_seeded_on_startup(client):
    response = client.get("/api/deals/", params={"active_only": False})
    assert response.status_code == 200
    deals = response.json()
    assert len(deals) == 15
    assert {d["deal_type"] for d in deals} == {"airline", "hotel", "tourism"}


def test_deals_filter_by_type(client):
    response = client.get("/api/deals/", params={"deal_type": "airline", "active_only": False})
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_deal_matched_to_seeded_destination(client):
    response = client.get("/api/deals/", params={"destination_id": 6, "active_only": False})  # Kyoto
    assert response.status_code == 200
    deals = response.json()
    assert len(deals) == 3
    assert {d["deal_type"] for d in deals} == {"airline", "hotel", "tourism"}


def test_get_deal_by_id(client):
    response = client.get("/api/deals/1")
    assert response.status_code == 200


def test_get_deal_404(client):
    response = client.get("/api/deals/9999")
    assert response.status_code == 404


def test_reingesting_deals_is_idempotent(client):
    before = client.get("/api/deals/", params={"active_only": False}).json()

    ingest_response = client.post("/api/deals/ingest")
    assert ingest_response.status_code == 200
    summary = ingest_response.json()
    assert summary["inserted"] == 0
    assert summary["updated"] == 15
    assert summary["errors"] == []

    after = client.get("/api/deals/", params={"active_only": False}).json()
    assert len(after) == len(before) == 15
