import os
import tempfile

import pytest

# Point the app at a throwaway SQLite file *before* app.db creates its engine,
# so the tests never touch the PostgreSQL database.
_db_dir = tempfile.mkdtemp(prefix="foundit-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_dir}/test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # "with" runs the lifespan hook, which creates the tables.
    # A bare TestClient(app) never does, and every DB call fails with "no such table: items".
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_item(client):
    """Factory: create an item through the API and return its JSON."""
    def _make(**overrides):
        payload = {
            "title": "Black umbrella",
            "type": "LOST",
            "category": "OTHER",
            "location": "Main gate",
            "reported_by": "Anshul",
        }
        payload.update(overrides)
        response = client.post("/api/items", json=payload)
        assert response.status_code == 201, response.text
        return response.json()
    return _make
