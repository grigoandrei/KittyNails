"""Removal-only bookings: the €15 price equals the deposit, nothing due at the studio."""

from datetime import datetime

from tests.conftest import at, future_weekday

MONDAY = future_weekday(0)


async def setup(client):
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0, "start_time": "09:00:00", "end_time": "18:00:00",
    })
    resp = await client.post("/api/admin/nail-types", json={
        "name": "Nail Removal", "duration_minutes": 30, "price": 15,
    })
    return resp.json()["id"]


async def test_book_removal_only(client):
    removal_id = await setup(client)
    resp = await client.post("/api/appointments", json={
        "nail_type_id": removal_id,
        "client_email": "mia@example.com",
        "start_time": at(MONDAY, 10),
    })
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["quoted_price"] == 15
    start = datetime.fromisoformat(body["start_time"])
    end = datetime.fromisoformat(body["end_time"])
    assert (end - start).total_seconds() == 30 * 60


async def test_removal_only_never_charges_removal_twice(client):
    removal_id = await setup(client)
    resp = await client.post("/api/appointments", json={
        "nail_type_id": removal_id,
        "client_email": "mia@example.com",
        "start_time": at(MONDAY, 10),
        "needs_removal": True,
    })
    assert resp.status_code == 201
    assert resp.json()["quoted_price"] == 15
    assert resp.json()["needs_removal"] is False


async def test_removal_only_rejects_design_tier(client):
    removal_id = await setup(client)
    tier = await client.post("/api/admin/design-tiers", json={
        "name": "Simple", "duration_minutes": 0, "price": 0,
    })
    resp = await client.post("/api/appointments", json={
        "nail_type_id": removal_id,
        "design_tier_id": tier.json()["id"],
        "client_email": "mia@example.com",
        "start_time": at(MONDAY, 10),
    })
    assert resp.status_code == 400


async def test_admin_edit_cannot_add_removal_to_removal_only(client):
    removal_id = await setup(client)
    appointment = (await client.post("/api/appointments", json={
        "nail_type_id": removal_id,
        "client_email": "mia@example.com",
        "start_time": at(MONDAY, 10),
    })).json()

    resp = await client.patch(
        f"/api/admin/appointments/{appointment['id']}", json={"needs_removal": True}
    )
    assert resp.status_code == 200
    assert resp.json()["needs_removal"] is False
    assert resp.json()["quoted_price"] == 15


async def test_admin_manual_booking_ignores_removal_for_removal_only(client):
    removal_id = await setup(client)
    resp = await client.post("/api/admin/appointments/", json={
        "nail_type_id": removal_id,
        "client_email": "mia@example.com",
        "start_time": at(MONDAY, 10),
        "needs_removal": True,
    })
    assert resp.status_code == 201
    assert resp.json()["quoted_price"] == 15
    assert resp.json()["needs_removal"] is False
