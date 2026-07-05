import pytest


async def create_test_service(client):
    """Helper to create a service and return its ID."""
    response = await client.post("/api/admin/services", json={
        "name": "Gel Nails",
        "duration_minutes": 60,
        "price": 45.00,
    })
    return response.json()["id"]


async def setup_availability_for_day(client, day_of_week):
    """Helper to create availability rules for a given day."""
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": day_of_week,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })


async def test_create_appointment(client):
    service_id = await create_test_service(client)
    # 2026-06-15 is a Monday (weekday 0)
    await setup_availability_for_day(client, 0)

    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "test@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["service_id"] == service_id
    assert data["client_email"] == "test@example.com"
    assert data["status"] == "BOOKED"


async def test_appointment_conflict_same_time(client):
    service_id = await create_test_service(client)
    await setup_availability_for_day(client, 0)

    await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "first@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })

    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "second@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })
    assert response.status_code == 409


async def test_appointment_conflict_overlapping(client):
    service_id = await create_test_service(client)
    await setup_availability_for_day(client, 0)

    await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "first@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })

    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "second@example.com",
        "start_time": "2026-06-15T10:30:00+00:00",
    })
    assert response.status_code == 409


async def test_appointment_no_conflict_adjacent(client):
    service_id = await create_test_service(client)
    await setup_availability_for_day(client, 0)

    await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "first@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })

    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "second@example.com",
        "start_time": "2026-06-15T11:00:00+00:00",
    })
    assert response.status_code == 201


async def test_appointment_nonexistent_service(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post("/api/appointments", json={
        "service_id": fake_id,
        "client_email": "test@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })
    assert response.status_code == 404


async def test_appointment_outside_working_hours(client):
    service_id = await create_test_service(client)
    await setup_availability_for_day(client, 0)

    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "test@example.com",
        "start_time": "2026-06-15T07:00:00+00:00",
    })
    assert response.status_code == 400


async def test_appointment_salon_closed(client):
    service_id = await create_test_service(client)
    # No availability rules for Sunday (6)
    # 2026-06-14 is a Sunday
    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "test@example.com",
        "start_time": "2026-06-14T10:00:00+00:00",
    })
    assert response.status_code == 400


async def test_appointment_during_blocked_time(client):
    service_id = await create_test_service(client)
    await setup_availability_for_day(client, 0)

    await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-06-15T12:00:00+00:00",
        "end_time": "2026-06-15T13:00:00+00:00",
        "reason": "Lunch break",
    })

    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "test@example.com",
        "start_time": "2026-06-15T12:00:00+00:00",
    })
    assert response.status_code == 409


async def test_canceled_appointment_does_not_block(client):
    service_id = await create_test_service(client)
    await setup_availability_for_day(client, 0)

    create_resp = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "first@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })
    appointment_id = create_resp.json()["id"]

    await client.patch(f"/api/admin/appointments/{appointment_id}/cancel")

    response = await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "second@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })
    assert response.status_code == 201
