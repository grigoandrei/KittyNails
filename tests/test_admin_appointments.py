import pytest


async def create_test_categories(client):
    nail_resp = await client.post("/api/admin/nail-types", json={
        "name": "Regular",
        "duration_minutes": 45,
        "price": 30.00,
    })
    design_resp = await client.post("/api/admin/design-tiers", json={
        "name": "Simple",
        "duration_minutes": 15,
        "price": 15.00,
    })
    return nail_resp.json()["id"], design_resp.json()["id"]


async def setup_availability_and_book(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })
    resp = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })
    return resp.json()["id"]


async def test_list_appointments(client):
    appointment_id = await setup_availability_and_book(client)

    response = await client.get("/api/admin/appointments/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == appointment_id


async def test_list_appointments_filter_by_status(client):
    appointment_id = await setup_availability_and_book(client)

    response = await client.get("/api/admin/appointments/?status=BOOKED")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await client.get("/api/admin/appointments/?status=CANCELED")
    assert response.status_code == 200
    assert len(response.json()) == 0


async def test_cancel_appointment(client):
    appointment_id = await setup_availability_and_book(client)

    response = await client.patch(f"/api/admin/appointments/{appointment_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELED"


async def test_no_show_appointment(client):
    appointment_id = await setup_availability_and_book(client)

    response = await client.patch(f"/api/admin/appointments/{appointment_id}/no-show")
    assert response.status_code == 200
    assert response.json()["status"] == "NO_SHOW"


async def test_complete_appointment(client):
    appointment_id = await setup_availability_and_book(client)

    response = await client.patch(f"/api/admin/appointments/{appointment_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


async def test_update_nonexistent_appointment(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.patch(f"/api/admin/appointments/{fake_id}/cancel")
    assert response.status_code == 404


async def test_list_appointments_pagination(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })

    for hour in range(9, 14):
        await client.post("/api/appointments", json={
            "nail_type_id": nail_type_id,
            "design_tier_id": design_tier_id,
            "client_email": f"client{hour}@example.com",
            "start_time": f"2026-08-10T{hour:02d}:00:00+00:00",
        })

    response = await client.get("/api/admin/appointments/?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = await client.get("/api/admin/appointments/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2
