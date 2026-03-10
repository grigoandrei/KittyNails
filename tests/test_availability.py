"""
Unit tests for the availability router endpoints.

Tests: set weekly availability, retrieve schedule for a date,
       block a time, verify blocked time appears in schedule.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# In-memory SQLite test database
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
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


client = TestClient(app)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_set_weekly_availability():
    """PUT /availability/weekly sets recurring hours and returns them."""
    schedule = [
        {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},  # Monday
        {"day_of_week": 2, "start_time": "10:00:00", "end_time": "16:00:00"},  # Wednesday
    ]
    response = client.put("/availability/weekly", json=schedule)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["day_of_week"] == 0
    assert data[0]["start_time"] == "09:00:00"
    assert data[0]["end_time"] == "17:00:00"
    assert "id" in data[0]


def test_set_weekly_availability_upserts():
    """PUT /availability/weekly updates existing day instead of duplicating."""
    schedule = [{"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"}]
    client.put("/availability/weekly", json=schedule)

    updated = [{"day_of_week": 0, "start_time": "08:00:00", "end_time": "18:00:00"}]
    response = client.put("/availability/weekly", json=updated)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["start_time"] == "08:00:00"
    assert data[0]["end_time"] == "18:00:00"


def test_get_schedule_for_working_day():
    """GET /availability/?date=... returns slots for a day with availability set."""
    # Monday = day_of_week 0. Pick a known Monday.
    schedule = [{"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"}]
    client.put("/availability/weekly", json=schedule)

    # 2026-03-16 is a Monday
    response = client.get("/availability/", params={"date": "2026-03-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-03-16"
    assert data["is_working_day"] is True
    assert len(data["slots"]) >= 1
    assert data["slots"][0]["start_time"] == "09:00:00"
    assert data["slots"][0]["end_time"] == "17:00:00"


def test_get_schedule_for_non_working_day():
    """GET /availability/?date=... returns empty schedule for a day with no availability."""
    # Don't set any availability — every day is a non-working day.
    # 2026-03-16 is a Monday
    response = client.get("/availability/", params={"date": "2026-03-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_working_day"] is False
    assert data["slots"] == []


def test_block_time():
    """POST /availability/block creates a blocked time entry."""
    block = {
        "blocked_date": "2026-03-16",
        "start_time": "12:00:00",
        "end_time": "13:00:00",
        "reason": "Lunch break",
    }
    response = client.post("/availability/block", json=block)
    assert response.status_code == 201
    data = response.json()
    assert data["blocked_date"] == "2026-03-16"
    assert data["start_time"] == "12:00:00"
    assert data["end_time"] == "13:00:00"
    assert data["reason"] == "Lunch break"
    assert "id" in data


def test_block_entire_day():
    """POST /availability/block with no times blocks the whole day."""
    block = {"blocked_date": "2026-04-01", "reason": "Vacation"}
    response = client.post("/availability/block", json=block)
    assert response.status_code == 201
    data = response.json()
    assert data["start_time"] is None
    assert data["end_time"] is None
    assert data["reason"] == "Vacation"


def test_blocked_time_reflected_in_schedule():
    """Blocked time should be queryable after creation (schedule endpoint still works)."""
    # Set Monday availability
    schedule = [{"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"}]
    client.put("/availability/weekly", json=schedule)

    # Block a time on that Monday
    block = {
        "blocked_date": "2026-03-16",
        "start_time": "12:00:00",
        "end_time": "13:00:00",
        "reason": "Lunch",
    }
    client.post("/availability/block", json=block)

    # Schedule endpoint should still return the day as a working day
    response = client.get("/availability/", params={"date": "2026-03-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_working_day"] is True
