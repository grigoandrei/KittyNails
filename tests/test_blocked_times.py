import pytest


async def test_create_blocked_time(client):
    response = await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-06-25T09:00:00Z",
        "end_time": "2026-06-25T17:00:00Z",
        "reason": "Holiday",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["start_time"] == "2026-06-25T09:00:00Z"
    assert data["end_time"] == "2026-06-25T17:00:00Z"
    assert data["reason"] == "Holiday"
    assert "id" in data


async def test_create_blocked_time_without_reason(client):
    response = await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-07-04T00:00:00Z",
        "end_time": "2026-07-04T23:59:00Z",
    })
    assert response.status_code == 201
    assert response.json()["reason"] is None


async def test_create_blocked_time_invalid_time_order(client):
    response = await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-06-25T17:00:00Z",
        "end_time": "2026-06-25T09:00:00Z",
    })
    assert response.status_code == 400


async def test_create_duplicate_blocked_time(client):
    await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-08-15T09:00:00Z",
        "end_time": "2026-08-15T17:00:00Z",
    })
    response = await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-08-15T09:00:00Z",
        "end_time": "2026-08-15T17:00:00Z",
    })
    assert response.status_code == 409


async def test_get_all_blocked_times(client):
    await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-06-25T09:00:00Z",
        "end_time": "2026-06-25T17:00:00Z",
    })
    await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-12-25T00:00:00Z",
        "end_time": "2026-12-25T23:59:00Z",
        "reason": "Christmas",
    })
    response = await client.get("/api/admin/blocked-times")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_delete_blocked_time(client):
    create_resp = await client.post("/api/admin/blocked-times", json={
        "start_time": "2026-09-01T10:00:00Z",
        "end_time": "2026-09-01T14:00:00Z",
    })
    time_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/admin/blocked-times/{time_id}")
    assert delete_resp.status_code == 204

    # Verify it's gone
    get_resp = await client.get("/api/admin/blocked-times")
    assert len(get_resp.json()) == 0


async def test_delete_nonexistent_blocked_time(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/api/admin/blocked-times/{fake_id}")
    assert response.status_code == 404
