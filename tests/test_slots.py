
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def _today() -> date:
    return datetime.now(BERLIN_TZ).date()


def next_weekday(weekday: int, min_ahead_days: int = 3) -> date:
    """Return the next date landing on `weekday` (0=Mon) at least
    `min_ahead_days` in the future.

    Slots in the past are filtered out by the service, so tests must target a
    future date. A few days of lead time keeps every slot on the day safely
    ahead of "now" regardless of the time the suite runs.
    """
    start = _today() + timedelta(days=min_ahead_days)
    offset = (weekday - start.weekday()) % 7
    return start + timedelta(days=offset)


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


def slot_times(slots):
    """Extract HH:MM strings (Berlin local) from returned ISO datetimes."""
    out = []
    for s in slots:
        dt = datetime.fromisoformat(s)
        out.append(dt.strftime("%H:%M"))
    return out


async def test_empty_day_shows_full_30min_grid(client):
    """An empty day shows every 30-minute start where the appointment fits."""
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    target = next_weekday(0)  # a Monday
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "10:00:00",
        "end_time": "12:00:00",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, target))
    assert response.status_code == 200
    times = slot_times(response.json())
    # 10:00-12:00 window, 60-min service, 30-min grid:
    # 10:00, 10:30, 11:00 (11:00+60=12:00 fits; 11:30+60=13:00 doesn't).
    assert times == ["10:00", "10:30", "11:00"]


async def test_available_slots_basic(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    target = next_weekday(0)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, target))
    assert response.status_code == 200
    times = slot_times(response.json())
    # 09:00-12:00, 60-min service, 30-min grid: last start is 11:00.
    assert times == ["09:00", "09:30", "10:00", "10:30", "11:00"]


async def test_available_slots_with_booking(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    target = next_weekday(0)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    # Book 10:00-11:00 (Berlin local).
    await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": f"{target}T10:00:00+02:00",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, target))
    assert response.status_code == 200
    times = slot_times(response.json())
    # Booking 10:00-11:00 knocks out any 60-min slot overlapping it:
    # 09:30 (09:30-10:30) and 10:00, 10:30 overlap; 09:00 (09:00-10:00) is fine,
    # 11:00 (11:00-12:00) is fine.
    assert times == ["09:00", "11:00"]


async def test_available_slots_with_blocked_time(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    target = next_weekday(0)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })

    await client.post("/api/admin/blocked-times", json={
        "start_time": f"{target}T10:00:00+02:00",
        "end_time": f"{target}T11:00:00+02:00",
        "reason": "Break",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, target))
    assert response.status_code == 200
    times = slot_times(response.json())
    # Same overlap logic as booking: 09:00 and 11:00 survive.
    assert times == ["09:00", "11:00"]


async def test_available_slots_closed_day(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    # No availability rules for Sunday (6).
    target = next_weekday(6)
    response = await client.get(slots_url(nail_type_id, design_tier_id, target))
    assert response.status_code == 200
    assert response.json() == []


async def test_available_slots_nonexistent_nail_type(client):
    _, design_tier_id = await create_test_categories(client, duration=60)
    fake_id = "00000000-0000-0000-0000-000000000000"
    target = next_weekday(0)
    response = await client.get(slots_url(fake_id, design_tier_id, target))
    assert response.status_code == 404


async def test_available_slots_nonexistent_design_tier(client):
    nail_type_id, _ = await create_test_categories(client, duration=60)
    fake_id = "00000000-0000-0000-0000-000000000000"
    target = next_weekday(0)
    response = await client.get(slots_url(nail_type_id, fake_id, target))
    assert response.status_code == 404


async def test_available_slots_different_durations(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=120)
    target = next_weekday(0)
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "13:00:00",
    })

    response = await client.get(slots_url(nail_type_id, design_tier_id, target))
    assert response.status_code == 200
    times = slot_times(response.json())
    # 09:00-13:00, 120-min service, 30-min grid: last start is 11:00.
    assert times == ["09:00", "09:30", "10:00", "10:30", "11:00"]


async def test_available_dates(client):
    nail_type_id, design_tier_id = await create_test_categories(client, duration=60)
    # Set availability for Monday (0) and Wednesday (2) only.
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

    target = next_weekday(0)
    response = await client.get(
        dates_url(nail_type_id, design_tier_id, target.year, target.month)
    )
    assert response.status_code == 200
    dates = response.json()
    # Only Mondays and Wednesdays that are today or later.
    assert len(dates) > 0
    for d in dates:
        parsed = date.fromisoformat(d)
        assert parsed.weekday() in (0, 2)
        assert parsed >= _today()


async def test_available_dates_nonexistent_nail_type(client):
    _, design_tier_id = await create_test_categories(client, duration=60)
    fake_id = "00000000-0000-0000-0000-000000000000"
    target = next_weekday(0)
    response = await client.get(
        dates_url(fake_id, design_tier_id, target.year, target.month)
    )
    assert response.status_code == 404
