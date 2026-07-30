"""Shared pytest fixtures for the backend test suite.

See documentation/testing.md for the full rationale. Key points:

- Tests run against a real temp-file SQLite database (not `:memory:`), since
  the app's connection pooling assumes a real file the way it would in dev.
- The FastAPI lifespan (create tables, seed sample data, run deal
  ingestion) runs exactly once for the whole session -- all of that is
  local/no-network, so it's fast and doesn't need repeating per test.
- Each test gets its own transactional `db_session`, joined to the engine's
  connection with `join_transaction_mode="create_savepoint"` so that the
  app code's own `db.commit()` calls (used throughout the real routes)
  become savepoint releases instead of ending the outer transaction --
  the whole thing is rolled back after each test, so tests can freely
  register users, add favorites, etc. without leaking state into others.
"""

import os
from pathlib import Path

_TEST_DB_PATH = Path(__file__).resolve().parent / "_test.db"
_TEST_DB_PATH.unlink(missing_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
# A key >=32 bytes avoids PyJWT's InsecureKeyLengthWarning noise in test output.
os.environ["SECRET_KEY"] = "pytest-only-test-secret-key-not-for-production-use"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.database.connection import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def _app_session():
    """Triggers the FastAPI lifespan (create_all + seed + deal ingestion)
    exactly once for the whole test session."""
    with TestClient(app) as test_client:
        yield test_client
    # Release every pooled connection before deleting the file -- on Windows
    # an open handle (even idle, pooled) blocks unlink() with a PermissionError.
    engine.dispose()
    _TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(_app_session, db_session):
    """A TestClient whose `get_db` dependency is overridden to use a
    per-test transactional session, isolating each test's writes."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield _app_session
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def auth_headers(client):
    """Registers a fresh user and returns an Authorization header for them."""

    def _register(email: str = "test.user@example.com", password: str = "hunter2222") -> dict[str, str]:
        response = client.post("/api/auth/register", json={"email": email, "password": password})
        assert response.status_code == 201, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _register
