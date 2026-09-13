from unittest.mock import patch

from tests.conftest import at, future_weekday

MONDAY = future_weekday(0)


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
        "start_time": at(MONDAY, 10),
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
    await setup_availability_and_book(client)

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
            "start_time": at(MONDAY, hour),
        })

    response = await client.get("/api/admin/appointments/?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = await client.get("/api/admin/appointments/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


@patch("src.routers.admin.appointment.generate_presigned_url")
async def test_admin_listing_returns_presigned_image_url(mock_presign, client):
    mock_presign.return_value = "https://signed.example/photo.jpg"
    nail_type_id, design_tier_id = await create_test_categories(client)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })
    await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "photo@example.com",
        "start_time": at(MONDAY, 10),
        "image_key": "nail-photos/abc123.jpg",
    })

    response = await client.get("/api/admin/appointments/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["image_url"] == "https://signed.example/photo.jpg"
    mock_presign.assert_called_once_with("nail-photos/abc123.jpg")


@patch("src.routers.admin.appointment.generate_presigned_url")
async def test_admin_listing_no_image_url_when_no_photo(mock_presign, client):
    mock_presign.return_value = None
    nail_type_id, _ = await create_test_categories(client)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })
    await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "client_email": "nophoto@example.com",
        "start_time": at(MONDAY, 10),
    })

    response = await client.get("/api/admin/appointments/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["image_url"] is None


async def _setup_availability(client):
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })


async def test_admin_manual_booking_creates_booked_instagram(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await _setup_availability(client)

    response = await client.post("/api/admin/appointments/", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "iguser@example.com",
        "start_time": at(MONDAY, 11),
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "BOOKED"
    assert data["source"] == "instagram"
    # 30 (nail) + 15 (design) = 45, no removal
    assert data["quoted_price"] == 45.00


async def test_admin_manual_booking_with_removal(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await _setup_availability(client)

    response = await client.post("/api/admin/appointments/", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "iguser@example.com",
        "start_time": at(MONDAY, 11),
        "needs_removal": True,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["needs_removal"] is True
    assert data["quoted_price"] == 60.00  # 45 + 15 removal


async def test_admin_manual_booking_respects_conflicts(client):
    nail_type_id, design_tier_id = await create_test_categories(client)
    await _setup_availability(client)

    first = await client.post("/api/admin/appointments/", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "a@example.com",
        "start_time": at(MONDAY, 11),
    })
    assert first.status_code == 201

    # Same slot → conflict
    second = await client.post("/api/admin/appointments/", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "b@example.com",
        "start_time": at(MONDAY, 11),
    })
    assert second.status_code == 409


async def test_web_booking_has_source_web(client):
    """Public bookings default to source=web."""
    nail_type_id, design_tier_id = await create_test_categories(client)
    await _setup_availability(client)

    resp = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "web@example.com",
        "start_time": at(MONDAY, 12),
    })
    assert resp.status_code == 201
    assert resp.json()["source"] == "web"


async def _book_at(client, hour, minute=0):
    """Create categories + Monday availability and book one appointment; return
    (appointment_id, nail_type_id, design_tier_id)."""
    nail_type_id, design_tier_id = await create_test_categories(client)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })
    resp = await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "edit@example.com",
        "start_time": at(MONDAY, hour, minute),
    })
    return resp.json()["id"], nail_type_id, design_tier_id


async def test_edit_appointment_change_time(client):
    appt_id, _, _ = await _book_at(client, 10)
    resp = await client.patch(f"/api/admin/appointments/{appt_id}", json={
        "start_time": at(MONDAY, 11),
    })
    assert resp.status_code == 200
    from datetime import datetime
    got = resp.json()["start_time"]
    assert datetime.fromisoformat(got) == datetime.fromisoformat(at(MONDAY, 11))


async def test_edit_appointment_change_duration(client):
    appt_id, _, _ = await _book_at(client, 10)
    # Default service duration is 60 min (45+15). Override to 120.
    resp = await client.patch(f"/api/admin/appointments/{appt_id}", json={
        "duration_minutes": 120,
    })
    assert resp.status_code == 200
    data = resp.json()
    from datetime import datetime
    start = datetime.fromisoformat(data["start_time"])
    end = datetime.fromisoformat(data["end_time"])
    assert (end - start).total_seconds() / 60 == 120


async def test_edit_appointment_toggle_removal_recomputes_price(client):
    appt_id, _, _ = await _book_at(client, 10)
    # Base 30 + 15 = 45; adding removal → 60.
    resp = await client.patch(f"/api/admin/appointments/{appt_id}", json={
        "needs_removal": True,
    })
    assert resp.status_code == 200
    assert resp.json()["needs_removal"] is True
    assert resp.json()["quoted_price"] == 60.00

    # Toggling back off → 45 again.
    resp = await client.patch(f"/api/admin/appointments/{appt_id}", json={
        "needs_removal": False,
    })
    assert resp.status_code == 200
    assert resp.json()["quoted_price"] == 45.00


async def test_edit_appointment_conflict_excludes_self(client):
    """Editing an appointment without moving it must not conflict with itself."""
    appt_id, _, _ = await _book_at(client, 10)
    resp = await client.patch(f"/api/admin/appointments/{appt_id}", json={
        "needs_removal": True,
    })
    assert resp.status_code == 200


async def test_edit_appointment_conflict_with_other(client):
    appt_id, nail_type_id, design_tier_id = await _book_at(client, 10)
    # Second booking at 12:00 (60 min → 12:00-13:00).
    await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "other@example.com",
        "start_time": at(MONDAY, 12),
    })
    # Move the first onto the second → conflict.
    resp = await client.patch(f"/api/admin/appointments/{appt_id}", json={
        "start_time": at(MONDAY, 12),
    })
    assert resp.status_code == 409


async def test_edit_appointment_outside_hours(client):
    appt_id, _, _ = await _book_at(client, 10)
    # Extend duration so it runs past 18:00 close (start 10:00 + 600 min).
    resp = await client.patch(f"/api/admin/appointments/{appt_id}", json={
        "duration_minutes": 600,
    })
    assert resp.status_code == 400


async def test_edit_nonexistent_appointment(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.patch(f"/api/admin/appointments/{fake_id}", json={
        "needs_removal": True,
    })
    assert resp.status_code == 404
