"""
Unit tests for the appointments router endpoints.

Tests the full booking flow and error cases:
- create service → set availability → get slots → book → verify → cancel → verify slot returns
- double booking (409), past date (422), non-quarter-hour time (422),
  outside working hours (400), not found (404)
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
# Helpers
# ---------------------------------------------------------------------------

VALID_SERVICE = {
    "name": "Gel Manicure",
    "description": "Classic gel manicure",
    "duration_minutes": 60,
    "price": 35.00,
}

# 2026-03-16 is a Monday (day_of_week=0)
FUTURE_MONDAY = "2026-03-16"

MONDAY_AVAILABILITY = [
    {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"}
]


def _create_service(payload=None):
    resp = client.post("/services/", json=payload or VALID_SERVICE)
    assert resp.status_code == 201
    return resp.json()


def _set_availability(schedule=None):
    resp = client.put("/availability/weekly", json=schedule or MONDAY_AVAILABILITY)
    assert resp.status_code == 200
    return resp.json()


def _book(service_id: int, date: str = FUTURE_MONDAY, time: str = "10:00:00"):
    return client.post("/appointments/", json={
        "client_name": "Alice",
        "client_phone": "555-0100",
        "service_id": service_id,
        "appointment_date": date,
        "appointment_time": time,
    })


# ---------------------------------------------------------------------------
# Full booking flow
# ---------------------------------------------------------------------------


def test_full_booking_flow():
    """
    End-to-end: create service → set availability → get slots →
    book appointment → verify booking → cancel → verify slot returns.
    """
    # 1. Create a service
    svc = _create_service()
    svc_id = svc["id"]

    # 2. Set weekly availability for Monday
    _set_availability()

    # 3. Get available slots
    slots_resp = client.get("/appointments/available", params={
        "date": FUTURE_MONDAY, "service_id": svc_id
    })
    assert slots_resp.status_code == 200
    slots = slots_resp.json()
    assert len(slots) > 0
    # 10:00 should be among available slots
    ten_am = next((s for s in slots if s["start_time"] == "10:00:00"), None)
    assert ten_am is not None

    # 4. Book the 10:00 slot
    book_resp = _book(svc_id)
    assert book_resp.status_code == 201
    appt = book_resp.json()
    appt_id = appt["id"]
    assert appt["client_name"] == "Alice"
    assert appt["appointment_date"] == FUTURE_MONDAY
    assert appt["appointment_time"] == "10:00:00"
    assert appt["end_time"] == "11:00:00"
    assert appt["status"] == "AppointmentStatus.CONFIRMED"  or appt["status"] == "confirmed"
    assert appt["service"]["id"] == svc_id

    # 5. Verify booking via GET
    get_resp = client.get(f"/appointments/{appt_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == appt_id

    # 6. Cancel the appointment
    cancel_resp = client.delete(f"/appointments/{appt_id}")
    assert cancel_resp.status_code == 204

    # 7. Verify the 10:00 slot is available again
    slots_after = client.get("/appointments/available", params={
        "date": FUTURE_MONDAY, "service_id": svc_id
    }).json()
    ten_am_after = next((s for s in slots_after if s["start_time"] == "10:00:00"), None)
    assert ten_am_after is not None


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_double_booking_returns_409():
    """Booking the same slot twice returns 409 Conflict."""
    svc = _create_service()
    _set_availability()

    first = _book(svc["id"])
    assert first.status_code == 201

    second = _book(svc["id"])
    assert second.status_code == 409


def test_past_date_returns_422():
    """Booking a past date is rejected by Pydantic validation (422)."""
    svc = _create_service()
    _set_availability()

    resp = _book(svc["id"], date="2020-01-01")
    assert resp.status_code == 422


def test_non_quarter_hour_returns_422():
    """Booking at a non-quarter-hour time is rejected (422)."""
    svc = _create_service()
    _set_availability()

    resp = _book(svc["id"], time="10:07:00")
    assert resp.status_code == 422


def test_outside_working_hours_returns_400():
    """Booking outside defined working hours returns 400."""
    svc = _create_service()
    _set_availability()  # 09:00–17:00

    # 07:00 is before working hours
    resp = _book(svc["id"], time="07:00:00")
    assert resp.status_code == 400


def test_get_nonexistent_appointment_returns_404():
    """GET /appointments/{id} returns 404 for a missing appointment."""
    resp = client.get("/appointments/9999")
    assert resp.status_code == 404


def test_cancel_nonexistent_appointment_returns_404():
    """DELETE /appointments/{id} returns 404 for a missing appointment."""
    resp = client.delete("/appointments/9999")
    assert resp.status_code == 404
