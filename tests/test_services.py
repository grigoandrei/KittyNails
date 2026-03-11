"""
Unit tests for the services router endpoints.

Tests: create a service (POST), list services (GET),
       update a service (PUT), 404 on updating a missing service.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# In-memory SQLite test database — single shared connection so tables
# created in the fixture are visible to the app's dependency override.
# ---------------------------------------------------------------------------

test_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables, override the dependency, yield, then tear down."""
    Base.metadata.create_all(bind=test_engine)

    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    def override_get_db():
        try:
            yield session
        finally:
            pass  # cleanup handled below

    app.dependency_overrides[get_db] = override_get_db
    yield
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_SERVICE = {
    "name": "Gel Manicure",
    "description": "Classic gel manicure",
    "duration_minutes": 60,
    "price": 35.00,
}

AUTH_HEADERS = {"Authorization": f"Bearer {os.environ.get('OWNER_TOKEN', 'test-token')}"}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_create_service():
    """POST /services/ creates a new service and returns it with an id."""
    response = client.post("/services/", json=VALID_SERVICE, headers=AUTH_HEADERS)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == VALID_SERVICE["name"]
    assert data["description"] == VALID_SERVICE["description"]
    assert data["duration_minutes"] == VALID_SERVICE["duration_minutes"]
    assert Decimal(data["price"]) == Decimal("35.00")
    assert "id" in data


def test_list_services():
    """GET /services/ returns all created services."""
    response = client.get("/services/")
    assert response.status_code == 200
    assert response.json() == []

    client.post("/services/", json=VALID_SERVICE, headers=AUTH_HEADERS)
    client.post("/services/", json={**VALID_SERVICE, "name": "Pedicure", "price": 40.00}, headers=AUTH_HEADERS)

    response = client.get("/services/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {s["name"] for s in data}
    assert names == {"Gel Manicure", "Pedicure"}


def test_update_service():
    """PUT /services/{id} updates an existing service."""
    create_resp = client.post("/services/", json=VALID_SERVICE, headers=AUTH_HEADERS)
    service_id = create_resp.json()["id"]

    update_payload = {"name": "Deluxe Gel Manicure", "price": 45.00}
    response = client.put(f"/services/{service_id}", json=update_payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Deluxe Gel Manicure"
    assert Decimal(data["price"]) == Decimal("45.00")
    assert data["duration_minutes"] == VALID_SERVICE["duration_minutes"]
    assert data["description"] == VALID_SERVICE["description"]


def test_update_missing_service_returns_404():
    """PUT /services/{id} returns 404 when the service doesn't exist."""
    response = client.put("/services/9999", json={"name": "Ghost Service"}, headers=AUTH_HEADERS)
    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"
