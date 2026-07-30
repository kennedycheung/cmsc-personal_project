def test_register_returns_token(client):
    response = client.post("/api/auth/register", json={"email": "alice@example.com", "password": "hunter2222"})
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_register_duplicate_email_rejected(client):
    payload = {"email": "bob@example.com", "password": "hunter2222"}
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 400


def test_register_rejects_short_password(client):
    response = client.post("/api/auth/register", json={"email": "short@example.com", "password": "abc"})
    assert response.status_code == 422


def test_login_success(client):
    client.post("/api/auth/register", json={"email": "carol@example.com", "password": "hunter2222"})
    response = client.post("/api/auth/login", json={"email": "carol@example.com", "password": "hunter2222"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"email": "dave@example.com", "password": "hunter2222"})
    response = client.post("/api/auth/login", json={"email": "dave@example.com", "password": "wrong-password"})
    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "hunter2222"})
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_rejects_garbage_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    headers = auth_headers("erin@example.com", "hunter2222")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "erin@example.com"
