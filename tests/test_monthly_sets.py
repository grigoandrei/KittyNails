"""Monthly sets: one-of-one designs that can be booked exactly once."""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from src.models.appointment import Appointment, Status
from src.services.s3_service import MONTHLY_SET_PREFIX
from tests.conftest import async_session_test, at, future_weekday

MONDAY = future_weekday(0)
PNG = ("design.png", b"\x89PNG fake bytes", "image/png")


@pytest.fixture(autouse=True)
def fake_s3():
    """No real S3 in tests. Uploads return a key and URLs are fake."""
    keys = iter(f"{MONTHLY_SET_PREFIX}/key-{i}.png" for i in range(1000))
    with (
        patch(
            "src.services.monthly_set_service.upload_nail_image",
            side_effect=lambda *a, **k: next(keys),
        ) as upload,
        patch(
            "src.services.monthly_set_service.generate_presigned_url",
            side_effect=lambda key: f"https://s3.test/{key}" if key else None,
        ),
        patch("src.services.monthly_set_service.delete_object") as delete,
    ):
        yield {"upload": upload, "delete": delete}


async def open_mondays(client):
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
    })


async def create_design(client, **overrides):
    form = {
        "title": "Cherry Blossom Aura",
        "price": "95",
        "duration_minutes": "120",
        "description": "Milky blush aura with tiny cherry blossoms.",
    }
    form.update(overrides)
    resp = await client.post("/api/admin/monthly-sets", data=form, files={"image": PNG})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def book(client, design_id, hour=10, email="mia@example.com", **extra):
    return await client.post("/api/appointments", json={
        "monthly_set_model_id": design_id,
        "client_email": email,
        "start_time": at(MONDAY, hour),
        **extra,
    })


async def admin_design(client, design_id):
    resp = await client.get("/api/admin/monthly-sets")
    return next(d for d in resp.json() if d["id"] == design_id)


async def public_ids(client):
    resp = await client.get("/api/monthly-sets")
    assert resp.status_code == 200
    return [d["id"] for d in resp.json()]


# ── Admin CRUD ──────────────────────────────────────────────────────────────


async def test_create_design(client, fake_s3):
    design = await create_design(client, title="  Pearl Glaze  ")

    assert design["title"] == "Pearl Glaze"
    assert design["price"] == 95
    assert design["duration_minutes"] == 120
    assert design["state"] == "available"
    assert design["has_bookings"] is False
    assert design["image_url"].startswith("https://s3.test/monthly-sets/")
    # Stored under its own prefix, not with client photos.
    assert fake_s3["upload"].call_args.args[2] == MONTHLY_SET_PREFIX


async def test_create_design_without_description(client):
    design = await create_design(client, description="   ")
    assert design["description"] is None


async def test_create_design_upload_failure_returns_502(client, fake_s3):
    fake_s3["upload"].side_effect = None
    fake_s3["upload"].return_value = None
    resp = await client.post(
        "/api/admin/monthly-sets",
        data={"title": "X", "price": "50", "duration_minutes": "60"},
        files={"image": PNG},
    )
    assert resp.status_code == 502


@pytest.mark.parametrize("field,value", [
    ("title", ""),
    ("title", "x" * 81),
    ("price", "0"),
    ("duration_minutes", "10"),
    ("duration_minutes", "601"),
    ("description", "x" * 501),
])
async def test_create_design_validation(client, field, value):
    form = {"title": "Ok", "price": "50", "duration_minutes": "60", field: value}
    resp = await client.post("/api/admin/monthly-sets", data=form, files={"image": PNG})
    assert resp.status_code == 422


async def test_create_design_rejects_non_image(client):
    resp = await client.post(
        "/api/admin/monthly-sets",
        data={"title": "Ok", "price": "50", "duration_minutes": "60"},
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


async def test_update_design(client):
    design = await create_design(client)
    resp = await client.put(f"/api/admin/monthly-sets/{design['id']}", json={
        "title": "Strawberry Milk",
        "price": 110,
        "duration_minutes": 150,
        "description": "",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Strawberry Milk"
    assert body["price"] == 110
    assert body["duration_minutes"] == 150
    assert body["description"] is None


async def test_update_rejects_blank_title(client):
    design = await create_design(client)
    resp = await client.put(f"/api/admin/monthly-sets/{design['id']}", json={"title": "  "})
    assert resp.status_code == 400


async def test_replace_image_deletes_old_photo(client, fake_s3):
    design = await create_design(client)
    old_url = design["image_url"]
    resp = await client.put(
        f"/api/admin/monthly-sets/{design['id']}/image", files={"image": PNG}
    )
    assert resp.status_code == 200
    assert resp.json()["image_url"] != old_url
    fake_s3["delete"].assert_called_once_with(old_url.removeprefix("https://s3.test/"))


async def test_hidden_design_not_public_and_not_bookable(client):
    await open_mondays(client)
    design = await create_design(client)
    await client.put(f"/api/admin/monthly-sets/{design['id']}", json={"is_active": False})

    assert design["id"] not in await public_ids(client)
    assert (await admin_design(client, design["id"]))["state"] == "hidden"
    assert (await book(client, design["id"])).status_code == 404


async def test_delete_never_booked_design(client, fake_s3):
    design = await create_design(client)
    resp = await client.delete(f"/api/admin/monthly-sets/{design['id']}")
    assert resp.status_code == 204
    assert (await client.get("/api/admin/monthly-sets")).json() == []
    fake_s3["delete"].assert_called_once()


async def test_delete_blocked_once_booked_even_after_cancel(client):
    await open_mondays(client)
    design = await create_design(client)
    appointment = (await book(client, design["id"])).json()
    await client.patch(f"/api/admin/appointments/{appointment['id']}/cancel")

    resp = await client.delete(f"/api/admin/monthly-sets/{design['id']}")
    assert resp.status_code == 409
    assert (await admin_design(client, design["id"]))["has_bookings"] is True


# ── Booking once ────────────────────────────────────────────────────────────


async def test_book_design_uses_its_price_and_duration(client):
    await open_mondays(client)
    design = await create_design(client, price="95", duration_minutes="120")

    resp = await book(client, design["id"])
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["monthly_set_model_id"] == design["id"]
    assert body["nail_type_id"] is None
    assert body["quoted_price"] == 95
    start = datetime.fromisoformat(body["start_time"])
    end = datetime.fromisoformat(body["end_time"])
    assert (end - start).total_seconds() == 120 * 60


async def test_book_design_with_removal(client):
    await open_mondays(client)
    design = await create_design(client, price="95")
    resp = await book(client, design["id"], needs_removal=True)
    assert resp.json()["quoted_price"] == 110


async def test_design_can_only_be_booked_once(client):
    await open_mondays(client)
    design = await create_design(client)

    assert (await book(client, design["id"], hour=10)).status_code == 201
    # Different client, different free time: still taken.
    second = await book(client, design["id"], hour=14, email="other@example.com")
    assert second.status_code == 409

    assert design["id"] not in await public_ids(client)
    admin = await admin_design(client, design["id"])
    assert admin["state"] == "booked"
    assert admin["client_email"] == "mia@example.com"


async def test_concurrent_bookings_only_one_wins(client):
    await open_mondays(client)
    design = await create_design(client)

    results = await asyncio.gather(
        book(client, design["id"], hour=10, email="a@example.com"),
        book(client, design["id"], hour=14, email="b@example.com"),
        book(client, design["id"], hour=15, email="c@example.com"),
    )
    codes = sorted(r.status_code for r in results)
    assert codes == [201, 409, 409]


@pytest.mark.parametrize("action", ["cancel", "no-show"])
async def test_cancel_or_no_show_frees_design(client, action):
    await open_mondays(client)
    design = await create_design(client)
    appointment = (await book(client, design["id"])).json()

    resp = await client.patch(f"/api/admin/appointments/{appointment['id']}/{action}")
    assert resp.status_code == 200

    assert design["id"] in await public_ids(client)
    assert (await book(client, design["id"], hour=14)).status_code == 201


async def test_completed_keeps_design_taken(client):
    await open_mondays(client)
    design = await create_design(client)
    appointment = (await book(client, design["id"])).json()
    await client.patch(f"/api/admin/appointments/{appointment['id']}/complete")

    assert design["id"] not in await public_ids(client)
    assert (await book(client, design["id"], hour=14)).status_code == 409


async def test_reviving_canceled_booking_conflicts_with_new_holder(client):
    await open_mondays(client)
    design = await create_design(client)
    first = (await book(client, design["id"])).json()
    await client.patch(f"/api/admin/appointments/{first['id']}/cancel")
    assert (await book(client, design["id"], hour=14)).status_code == 201

    resp = await client.patch(f"/api/admin/appointments/{first['id']}/complete")
    assert resp.status_code == 409


async def test_price_edit_does_not_change_existing_booking(client):
    await open_mondays(client)
    design = await create_design(client, price="95")
    appointment = (await book(client, design["id"])).json()

    await client.put(f"/api/admin/monthly-sets/{design['id']}", json={"price": 200})

    rows = (await client.get("/api/admin/appointments/")).json()
    assert next(r for r in rows if r["id"] == appointment["id"])["quoted_price"] == 95


async def test_db_index_blocks_second_live_appointment(client):
    """The partial unique index is the last line of defense."""
    design = await create_design(client)
    start = datetime.fromisoformat(at(MONDAY, 10))

    def appointment(status):
        return Appointment(
            monthly_set_model_id=design["id"],
            client_email="x@example.com",
            start_time=start,
            end_time=start,
            status=status,
            quoted_price=95,
        )

    async with async_session_test() as db:
        db.add(appointment(Status.CANCELED))
        db.add(appointment(Status.BOOKED))
        await db.commit()
        db.add(appointment(Status.PENDING_PAYMENT))
        with pytest.raises(IntegrityError):
            await db.commit()


# ── Request validation ──────────────────────────────────────────────────────


async def test_booking_needs_exactly_one_service(client):
    await open_mondays(client)
    design = await create_design(client)
    nail = await client.post("/api/admin/nail-types", json={
        "name": "Regular", "duration_minutes": 90, "price": 40,
    })

    both = await book(client, design["id"], nail_type_id=nail.json()["id"])
    assert both.status_code == 422

    neither = await client.post("/api/appointments", json={
        "client_email": "mia@example.com", "start_time": at(MONDAY, 10),
    })
    assert neither.status_code == 422


async def test_booking_design_rejects_design_tier(client):
    await open_mondays(client)
    design = await create_design(client)
    tier = await client.post("/api/admin/design-tiers", json={
        "name": "Simple", "duration_minutes": 0, "price": 0,
    })
    resp = await book(client, design["id"], design_tier_id=tier.json()["id"])
    assert resp.status_code == 422


# ── Slots ───────────────────────────────────────────────────────────────────


async def test_slots_for_design_use_its_duration(client):
    await open_mondays(client)
    design = await create_design(client, duration_minutes="480")

    resp = await client.get(
        "/api/slots/", params={"monthly_set_model_id": design["id"], "date": str(MONDAY)}
    )
    assert resp.status_code == 200
    # 09:00 to 18:00 fits an 8h appointment starting 09:00 or 09:30 or 10:00.
    assert len(resp.json()) == 3

    dates = await client.get("/api/slots/dates", params={
        "monthly_set_model_id": design["id"],
        "year": MONDAY.year,
        "month": MONDAY.month,
    })
    assert dates.status_code == 200
    assert str(MONDAY) in dates.json()


async def test_slots_for_taken_design_conflict(client):
    await open_mondays(client)
    design = await create_design(client)
    await book(client, design["id"])
    resp = await client.get(
        "/api/slots/", params={"monthly_set_model_id": design["id"], "date": str(MONDAY)}
    )
    assert resp.status_code == 409


async def test_slots_need_exactly_one_service(client):
    resp = await client.get("/api/slots/", params={"date": str(MONDAY)})
    assert resp.status_code == 422


# ── Stripe checkout ─────────────────────────────────────────────────────────


@patch("src.services.stripe_service._create_stripe_session")
async def test_checkout_reserves_design_with_short_expiry(mock_session, client):
    await open_mondays(client)
    design = await create_design(client)
    mock_session.return_value = MagicMock(id="cs_test_1", url="https://stripe.test/cs_1")

    resp = await client.post("/api/checkout/create-session", json={
        "monthly_set_model_id": design["id"],
        "client_email": "mia@example.com",
        "start_time": at(MONDAY, 10),
    })
    assert resp.status_code == 201

    _, _, service_name, expires_at = mock_session.call_args.args
    assert service_name == "Monthly set: Cherry Blossom Aura"
    assert expires_at is not None
    assert (await admin_design(client, design["id"]))["state"] == "reserved"
    assert design["id"] not in await public_ids(client)


@patch("src.services.stripe_service._create_stripe_session")
async def test_checkout_stripe_failure_releases_design(mock_session, client):
    await open_mondays(client)
    design = await create_design(client)
    mock_session.side_effect = RuntimeError("stripe down")

    with pytest.raises(RuntimeError):
        await client.post("/api/checkout/create-session", json={
            "monthly_set_model_id": design["id"],
            "client_email": "mia@example.com",
            "start_time": at(MONDAY, 10),
        })

    assert design["id"] in await public_ids(client)
