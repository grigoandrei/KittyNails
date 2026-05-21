import pytest


async def create_test_service(client):
    """Helper to create a service and return its ID."""
    response = await client.post("/api/admin/services", json={
        "name": "Gel Nails",
        "duration_minutes": 60,
        "price": 45.00,
    })
    return response.json()["id"]


async def test_create_appointment(client):
    service_id = await create_test_service(client)

    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "test@example.com",
        "start_time": "2026-06-15T10:00:00",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["service_id"] == service_id
    assert data["client_email"] == "test@example.com"
    assert data["status"] == "BOOKED"
    assert data["start_time"] == "2026-06-15T10:00:00"
    assert data["end_time"] == "2026-06-15T11:00:00"


async def test_appointment_conflict_same_time(client):
    service_id = await create_test_service(client)

    await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "first@example.com",
        "start_time": "2026-06-15T10:00:00",
    })

    # Same exact time slot
    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "second@example.com",
        "start_time": "2026-06-15T10:00:00",
    })
    assert response.status_code == 409


async def test_appointment_conflict_overlapping(client):
    service_id = await create_test_service(client)

    # Book 10:00 - 11:00
    await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "first@example.com",
        "start_time": "2026-06-15T10:00:00",
    })

    # Try to book 10:30 - 11:30 (overlaps)
    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "second@example.com",
        "start_time": "2026-06-15T10:30:00",
    })
    assert response.status_code == 409


async def test_appointment_no_conflict_adjacent(client):
    service_id = await create_test_service(client)

    # Book 10:00 - 11:00
    await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "first@example.com",
        "start_time": "2026-06-15T10:00:00",
    })

    # Book 11:00 - 12:00 (adjacent, no overlap)
    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "second@example.com",
        "start_time": "2026-06-15T11:00:00",
    })
    assert response.status_code == 201


async def test_appointment_nonexistent_service(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post("/api/appointments", json={
        "service_id": fake_id,
        "client_email": "test@example.com",
        "start_time": "2026-06-15T10:00:00",
    })
    assert response.status_code == 404
