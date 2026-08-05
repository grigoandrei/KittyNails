import pytest


async def create_test_categories(client, nail_minutes=45, design_minutes=15):
    """Create a nail type + design tier and return (nail_type_id, design_tier_id).
    Defaults sum to a 60-minute appointment to keep slot math simple."""
    nail_resp = await client.post("/api/admin/nail-types", json={
        "name": f"Nail {nail_minutes}min",
        "duration_minutes": nail_minutes,
        "price": 30.00,
    })
    design_resp = await client.post("/api/admin/design-tiers", json={
        "name": f"Design {design_minutes}min",
        "duration_minutes": design_minutes,
        "price": 15.00,
    })
    return nail_resp.json()["id"], design_resp.json()["id"]


async def setup_availability_for_day(client, day_of_week):
    """Helper to create availability rules for a given day."""
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": day_of_week,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })


async def test_create_appointment(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    # 2026-08-10 is a Monday (weekday 0)
    await setup_availability_for_day(client, 0)

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["nail_type_id"] == nail_type_id
    assert data["design_tier_id"] == design_tier_id
    assert data["client_email"] == "test@example.com"
    assert data["status"] == "BOOKED"
    # Price is derived server-side: 30 (nail) + 15 (design) = 45
    assert data["quoted_price"] == 45.00


async def test_create_appointment_persists_ai_fields(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await setup_availability_for_day(client, 0)

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
        "ai_confidence": "high",
        "ai_reasoning": "Clear photo of extended nails with simple design.",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["ai_confidence"] == "high"
    assert data["ai_reasoning"] == "Clear photo of extended nails with simple design."


async def test_appointment_conflict_same_time(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await setup_availability_for_day(client, 0)

    await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "first@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "second@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })
    assert response.status_code == 409


async def test_appointment_conflict_overlapping(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await setup_availability_for_day(client, 0)

    await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "first@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "second@example.com",
        "start_time": "2026-08-10T10:30:00+00:00",
    })
    assert response.status_code == 409


async def test_appointment_no_conflict_adjacent(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await setup_availability_for_day(client, 0)

    await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "first@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "second@example.com",
        "start_time": "2026-08-10T11:00:00+00:00",
    })
    assert response.status_code == 201


async def test_appointment_nonexistent_nail_type(client):
    _, design_tier_id = await create_test_categories(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post("/api/appointments", json={
        "nail_type_id": fake_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })
    assert response.status_code == 404


async def test_appointment_nonexistent_design_tier(client):
    nail_type_id, _ = await create_test_categories(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": fake_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })
    assert response.status_code == 404


async def test_appointment_outside_working_hours(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await setup_availability_for_day(client, 0)

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T07:00:00+00:00",
    })
    assert response.status_code == 400


async def test_appointment_salon_closed(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    # No availability rules for Sunday (6)
    # 2026-08-09 is a Sunday
    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-09T10:00:00+00:00",
    })
    assert response.status_code == 400


async def test_appointment_during_blocked_time(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await setup_availability_for_day(client, 0)

    await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-08-10T12:00:00+00:00",
        "end_time": "2026-08-10T13:00:00+00:00",
        "reason": "Lunch break",
    })

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T12:00:00+00:00",
    })
    assert response.status_code == 409


async def test_canceled_appointment_does_not_block(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await setup_availability_for_day(client, 0)

    create_resp = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "first@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })
    appointment_id = create_resp.json()["id"]

    await client.patch(f"/api/admin/appointments/{appointment_id}/cancel")

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "second@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })
    assert response.status_code == 201


async def test_inactive_nail_type_cannot_be_booked(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await setup_availability_for_day(client, 0)
    await client.put(f"/api/admin/nail-types/{nail_type_id}", json={"is_active": False})

    response = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })
    assert response.status_code == 404
