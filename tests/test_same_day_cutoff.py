"""Same-day booking cutoff: clients can't book for today once Berlin time
reaches SAME_DAY_CUTOFF_HOUR (14:00). Admin manual bookings are exempt.

"now" is frozen by patching slots_service.now_berlin to a time on a future
Monday, so the target date counts as "today" while still passing the
"must be in the future" schema validator (which uses the real clock).
"""
from datetime import datetime, time, timedelta
from unittest.mock import patch

from tests.conftest import BERLIN_TZ, at, future_weekday

MONDAY = future_weekday(0)
NOW_PATH = "src.services.slots_service.now_berlin"


def frozen(day, hour):
    return datetime.combine(day, time(hour), tzinfo=BERLIN_TZ)


async def setup(client):
    nail = await client.post("/api/admin/nail-types", json={
        "name": "Regular", "duration_minutes": 45, "price": 30.00,
    })
    design = await client.post("/api/admin/design-tiers", json={
        "name": "Simple", "duration_minutes": 15, "price": 15.00,
    })
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0, "start_time": "09:00:00", "end_time": "18:00:00",
    })
    return nail.json()["id"], design.json()["id"]


def slots_url(nail_type_id, design_tier_id, day):
    return (
        f"/api/slots/?nail_type_id={nail_type_id}"
        f"&design_tier_id={design_tier_id}&date={day}"
    )


def booking(nail_type_id, design_tier_id, start):
    return {
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": start,
    }


async def test_no_same_day_slots_after_cutoff(client):
    nail_type_id, design_tier_id = await setup(client)
    with patch(NOW_PATH, return_value=frozen(MONDAY, 15)):
        response = await client.get(slots_url(nail_type_id, design_tier_id, MONDAY))
    assert response.status_code == 200
    assert response.json() == []


async def test_same_day_slots_before_cutoff(client):
    nail_type_id, design_tier_id = await setup(client)
    with patch(NOW_PATH, return_value=frozen(MONDAY, 13)):
        response = await client.get(slots_url(nail_type_id, design_tier_id, MONDAY))
    slots = response.json()
    assert slots
    # Only slots after "now" are offered.
    assert all(datetime.fromisoformat(s) > frozen(MONDAY, 13) for s in slots)


async def test_cutoff_does_not_affect_tomorrow(client):
    nail_type_id, design_tier_id = await setup(client)
    sunday = MONDAY - timedelta(days=1)
    with patch(NOW_PATH, return_value=frozen(sunday, 20)):
        response = await client.get(slots_url(nail_type_id, design_tier_id, MONDAY))
    assert response.json()


async def test_today_hidden_from_calendar_after_cutoff(client):
    nail_type_id, design_tier_id = await setup(client)
    url = (
        f"/api/slots/dates?nail_type_id={nail_type_id}"
        f"&design_tier_id={design_tier_id}&year={MONDAY.year}&month={MONDAY.month}"
    )
    with patch(NOW_PATH, return_value=frozen(MONDAY, 15)):
        response = await client.get(url)
    assert str(MONDAY) not in response.json()


async def test_same_day_booking_rejected_after_cutoff(client):
    nail_type_id, design_tier_id = await setup(client)
    with patch(NOW_PATH, return_value=frozen(MONDAY, 15)):
        response = await client.post(
            "/api/appointments",
            json=booking(nail_type_id, design_tier_id, at(MONDAY, 15)),
        )
    assert response.status_code == 400
    assert "Same-day bookings close" in response.json()["detail"]


async def test_same_day_booking_allowed_before_cutoff(client):
    nail_type_id, design_tier_id = await setup(client)
    with patch(NOW_PATH, return_value=frozen(MONDAY, 13)):
        response = await client.post(
            "/api/appointments",
            json=booking(nail_type_id, design_tier_id, at(MONDAY, 15)),
        )
    assert response.status_code == 201


async def test_admin_booking_exempt_from_cutoff(client):
    nail_type_id, design_tier_id = await setup(client)
    with patch(NOW_PATH, return_value=frozen(MONDAY, 15)):
        response = await client.post(
            "/api/admin/appointments/",
            json=booking(nail_type_id, design_tier_id, at(MONDAY, 15)),
        )
    assert response.status_code == 201
