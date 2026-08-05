import pytest


async def create_test_categories(client, duration=60):
    """Create a nail type + design tier whose durations sum to `duration`.
    The design tier is a fixed 15 min; the nail type takes the remainder."""
    design_minutes = 15
    nail_minutes = duration - design_minutes
    nail_resp = await client.post("/api/admin/nail-types", json={
        "name": f"Nail {duration}min",
        "duration_minutes": nail_minutes,
        "price": 30.00,
    })
    design_resp = await client.post("/api/admin/design-tiers", json={
        "name": f"Design {duration}min",
        "duration_minutes": design_minutes,
        "price": 15.00,
    })
    return nail_resp.json()["id"], design_resp.json()["id"]


def slots_url(nail_type_id, design_tier_id, target_date):
    return (
        f"/api/slots/?nail_type_id={nail_type_id}"
        f"&design_tier_id={design_tier_id}&date={target_date}"
    )


def dates_url(nail_type_id, design_tier_id, year, month):
    return (
        f"/api/slots/dates?nail_type_id={nail_type_id}"
        f"&design_tier_id={design_tier_id}&year={year}&month={month}"
    )


async def test_available_slots_basic(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    # 2026-08-10 is Monday (weekday 0)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, "2026-08-10"))
    assert response.status_code == 200
    slots = response.json()
    # 3 hours / 60 min total = 3 slots: 9:00, 10:00, 11:00
    assert len(slots) == 3


async def test_available_slots_with_booking(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": "2026-08-10T10:00:00+00:00",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, "2026-08-10"))
    assert response.status_code == 200
    slots = response.json()
    # 10:00 is booked, so only 9:00 and 11:00 remain
    assert len(slots) == 2


async def test_available_slots_with_blocked_time(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-08-10T10:00:00+00:00",
        "end_time": "2026-08-10T11:00:00+00:00",
        "reason": "Break",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, "2026-08-10"))
    assert response.status_code == 200
    slots = response.json()
    # 10:00 is blocked, so only 9:00 and 11:00 remain
    assert len(slots) == 2


async def test_available_slots_closed_day(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    # No availability rules for Sunday (6)
    # 2026-08-09 is a Sunday
    response = await client.get(slots_url(nail_type_id, design_tier_id, "2026-08-09"))
    assert response.status_code == 200
    assert response.json() == []


async def test_available_slots_nonexistent_nail_type(client):
    _, design_tier_id = await create_test_categories(client, duration=60)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(slots_url(fake_id, design_tier_id, "2026-08-10"))
    assert response.status_code == 404


async def test_available_slots_nonexistent_design_tier(client):
    nail_type_id, _ = await create_test_categories(client, duration=60)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(slots_url(nail_type_id, fake_id, "2026-08-10"))
    assert response.status_code == 404


async def test_available_slots_different_durations(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=120)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "13:00:00",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, "2026-08-10"))
    assert response.status_code == 200
    slots = response.json()
    # 4 hours / 120 min total = 2 slots: 9:00, 11:00
    assert len(slots) == 2


async def test_available_dates(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
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

    response = await client.get(dates_url(nail_type_id, design_tier_id, 2026, 8))
    assert response.status_code == 200
    dates = response.json()
    # Should only contain Mondays and Wednesdays in August 2026 that are today or later
    assert len(dates) > 0
    for d in dates:
        assert "2026-08" in d


async def test_available_dates_nonexistent_nail_type(client):
    _, design_tier_id = await create_test_categories(client, duration=60)
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(dates_url(fake_id, design_tier_id, 2026, 8))
    assert response.status_code == 404
