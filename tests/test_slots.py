import pytest


async def create_test_service(client, duration=60):
    response = await client.post("/api/admin/services", json={
        "name": f"Service {duration}min",
        "duration_minutes": duration,
        "price": 45.00,
    })
    return response.json()["id"]


async def test_available_slots_basic(client):
    service_id = await create_test_service(client, duration=60)
    # 2026-06-15 is Monday (weekday 0)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    response = await client.get(f"/api/slots/?service_id={service_id}&date=2026-06-15")
    assert response.status_code == 200
    slots = response.json()
    # 3 hours / 60 min service = 3 slots: 9:00, 10:00, 11:00
    assert len(slots) == 3


async def test_available_slots_with_booking(client):
    service_id = await create_test_service(client, duration=60)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    await client.post("/api/appointments", json={
        "service_id": service_id,
        "client_email": "test@example.com",
        "start_time": "2026-06-15T10:00:00+00:00",
    })

    response = await client.get(f"/api/slots/?service_id={service_id}&date=2026-06-15")
    assert response.status_code == 200
    slots = response.json()
    # 10:00 is booked, so only 9:00 and 11:00 remain
    assert len(slots) == 2


async def test_available_slots_with_blocked_time(client):
    service_id = await create_test_service(client, duration=60)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-06-15T10:00:00+00:00",
        "end_time": "2026-06-15T11:00:00+00:00",
        "reason": "Break",
    })

    response = await client.get(f"/api/slots/?service_id={service_id}&date=2026-06-15")
    assert response.status_code == 200
    slots = response.json()
    # 10:00 is blocked, so only 9:00 and 11:00 remain
    assert len(slots) == 2


async def test_available_slots_closed_day(client):
    service_id = await create_test_service(client, duration=60)
    # No availability rules for Sunday (6)
    # 2026-06-14 is a Sunday
    response = await client.get(f"/api/slots/?service_id={service_id}&date=2026-06-14")
    assert response.status_code == 200
    assert response.json() == []


async def test_available_slots_nonexistent_service(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/slots/?service_id={fake_id}&date=2026-06-15")
    assert response.status_code == 404


async def test_available_slots_different_durations(client):
    service_id = await create_test_service(client, duration=120)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "13:00:00",
    })

    response = await client.get(f"/api/slots/?service_id={service_id}&date=2026-06-15")
    assert response.status_code == 200
    slots = response.json()
    # 4 hours / 120 min service = 2 slots: 9:00, 11:00
    assert len(slots) == 2


async def test_available_dates(client):
    service_id = await create_test_service(client, duration=60)
    # Set availability for Monday (0) and Wednesday (2) only
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 2,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    response = await client.get(f"/api/slots/dates?service_id={service_id}&year=2026&month=6")
    assert response.status_code == 200
    dates = response.json()
    # Should only contain Mondays and Wednesdays in June 2026 that are today or later
    assert len(dates) > 0
    for d in dates:
        assert "2026-06" in d


async def test_available_dates_nonexistent_service(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/slots/dates?service_id={fake_id}&year=2026&month=6")
    assert response.status_code == 404
