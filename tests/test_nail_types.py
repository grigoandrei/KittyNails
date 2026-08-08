async def test_create_nail_type(client):
    response = await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Regular",
            "duration_minutes": 75,
            "price": 40.00,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Regular"
    assert data["duration_minutes"] == 75
    assert data["price"] == 40.00
    assert data["is_active"] is True
    assert data["sort_order"] == 0
    assert "id" in data


async def test_create_nail_type_with_sort_order(client):
    response = await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Extensions",
            "duration_minutes": 120,
            "price": 55.00,
            "sort_order": 3,
        },
    )
    assert response.status_code == 201
    assert response.json()["sort_order"] == 3


async def test_create_duplicate_nail_type(client):
    await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Regular",
            "duration_minutes": 75,
            "price": 40.00,
        },
    )
    response = await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Regular",
            "duration_minutes": 30,
            "price": 25.00,
        },
    )
    assert response.status_code == 409


async def test_update_nail_type(client):
    create_resp = await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Regular",
            "duration_minutes": 75,
            "price": 40.00,
        },
    )
    nail_type_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/admin/nail-types/{nail_type_id}",
        json={
            "price": 45.00,
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["price"] == 45.00
    assert update_resp.json()["name"] == "Regular"  # unchanged


async def test_update_nonexistent_nail_type(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.put(
        f"/api/admin/nail-types/{fake_id}",
        json={
            "price": 50.00,
        },
    )
    assert response.status_code == 404


async def test_get_all_nail_types(client):
    await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Regular",
            "duration_minutes": 75,
            "price": 40.00,
        },
    )
    await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Extensions",
            "duration_minutes": 120,
            "price": 55.00,
        },
    )
    response = await client.get("/api/admin/nail-types")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_active_nail_types_excludes_inactive(client):
    create_resp = await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Old Type",
            "duration_minutes": 30,
            "price": 20.00,
        },
    )
    nail_type_id = create_resp.json()["id"]
    await client.put(
        f"/api/admin/nail-types/{nail_type_id}",
        json={
            "is_active": False,
        },
    )

    await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Active Type",
            "duration_minutes": 60,
            "price": 50.00,
        },
    )

    # Public endpoint should only show active
    response = await client.get("/api/nail-types")
    assert response.status_code == 200
    nail_types = response.json()
    assert len(nail_types) == 1
    assert nail_types[0]["name"] == "Active Type"


async def test_get_active_nail_types_ordered_by_sort_order(client):
    await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Third",
            "duration_minutes": 60,
            "price": 30.00,
            "sort_order": 3,
        },
    )
    await client.post(
        "/api/admin/nail-types",
        json={
            "name": "First",
            "duration_minutes": 60,
            "price": 30.00,
            "sort_order": 1,
        },
    )
    await client.post(
        "/api/admin/nail-types",
        json={
            "name": "Second",
            "duration_minutes": 60,
            "price": 30.00,
            "sort_order": 2,
        },
    )

    response = await client.get("/api/nail-types")
    assert response.status_code == 200
    names = [nt["name"] for nt in response.json()]
    assert names == ["First", "Second", "Third"]
