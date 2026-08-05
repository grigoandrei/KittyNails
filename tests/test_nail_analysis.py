import io
from types import SimpleNamespace
from unittest.mock import patch

from src.schemas.nail_analysis import (
    Confidence,
    DesignTierLabel,
    NailClassification,
    NailTypeLabel,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_parsed_message(classification: NailClassification | None, stop_reason: str = "end_turn"):
    """Mimic the anthropic ParsedMessage surface our service touches:
    `.stop_reason` and `.parsed_output`."""
    return SimpleNamespace(stop_reason=stop_reason, parsed_output=classification)


def mock_client_returning(classification, stop_reason="end_turn"):
    """Build a stand-in for AnthropicBedrock whose messages.parse(...) returns
    a fixed ParsedMessage. get_client() is patched to return this."""
    message = make_parsed_message(classification, stop_reason)
    parse = lambda **kwargs: message
    return SimpleNamespace(messages=SimpleNamespace(parse=parse))


async def seed_categories(client):
    """Seed the 3x3 vocabulary the AI can classify into, matching the enum labels."""
    for name, price, dur, order in [
        ("Short", 30.0, 60, 1),
        ("Regular", 40.0, 75, 2),
        ("Extensions", 55.0, 120, 3),
    ]:
        await client.post("/api/admin/nail-types", json={
            "name": name, "price": price, "duration_minutes": dur, "sort_order": order,
        })
    for name, price, dur, order in [
        ("Simple", 10.0, 15, 1),
        ("Medium", 25.0, 45, 2),
        ("Advanced", 45.0, 90, 3),
    ]:
        await client.post("/api/admin/design-tiers", json={
            "name": name, "price": price, "duration_minutes": dur, "sort_order": order,
        })


def fake_image_file():
    return {"image": ("nails.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_analyze_nails_happy_path(client):
    await seed_categories(client)
    classification = NailClassification(
        nail_type=NailTypeLabel.EXTENSIONS,
        design_tier=DesignTierLabel.ADVANCED,
        confidence=Confidence.HIGH,
        reasoning="Long extended nails with intricate hand-painted art.",
    )

    with patch(
        "src.services.nail_analysis_service.get_client",
        return_value=mock_client_returning(classification),
    ):
        response = await client.post("/api/analyze-nails", files=fake_image_file())

    assert response.status_code == 200
    data = response.json()
    assert data["nail_type"] == "Extensions"
    assert data["design_tier"] == "Advanced"
    # Price/duration derived server-side: 55 + 45 = 100, 120 + 90 = 210
    assert data["estimated_price"] == 100.0
    assert data["estimated_duration_minutes"] == 210
    assert data["confidence"] == "high"
    assert "nail_type_id" in data and "design_tier_id" in data


async def test_analyze_nails_pricing_short_simple(client):
    await seed_categories(client)
    classification = NailClassification(
        nail_type=NailTypeLabel.SHORT,
        design_tier=DesignTierLabel.SIMPLE,
        confidence=Confidence.MEDIUM,
        reasoning="Short natural nails, single colour.",
    )

    with patch(
        "src.services.nail_analysis_service.get_client",
        return_value=mock_client_returning(classification),
    ):
        response = await client.post("/api/analyze-nails", files=fake_image_file())

    assert response.status_code == 200
    data = response.json()
    # 30 + 10 = 40, 60 + 15 = 75
    assert data["estimated_price"] == 40.0
    assert data["estimated_duration_minutes"] == 75


async def test_analyze_nails_refusal(client):
    await seed_categories(client)

    with patch(
        "src.services.nail_analysis_service.get_client",
        return_value=mock_client_returning(None, stop_reason="refusal"),
    ):
        response = await client.post("/api/analyze-nails", files=fake_image_file())

    assert response.status_code == 400


async def test_analyze_nails_unparseable(client):
    await seed_categories(client)

    with patch(
        "src.services.nail_analysis_service.get_client",
        return_value=mock_client_returning(None, stop_reason="end_turn"),
    ):
        response = await client.post("/api/analyze-nails", files=fake_image_file())

    assert response.status_code == 400


async def test_analyze_nails_category_deactivated(client):
    """AI returns a valid label, but that category is inactive in the DB."""
    await seed_categories(client)
    # Deactivate Extensions
    admin = await client.get("/api/admin/nail-types")
    ext = next(nt for nt in admin.json() if nt["name"] == "Extensions")
    await client.put(f"/api/admin/nail-types/{ext['id']}", json={"is_active": False})

    classification = NailClassification(
        nail_type=NailTypeLabel.EXTENSIONS,
        design_tier=DesignTierLabel.SIMPLE,
        confidence=Confidence.HIGH,
        reasoning="Extended nails.",
    )

    with patch(
        "src.services.nail_analysis_service.get_client",
        return_value=mock_client_returning(classification),
    ):
        response = await client.post("/api/analyze-nails", files=fake_image_file())

    assert response.status_code == 404


async def test_analyze_nails_unsupported_media_type(client):
    await seed_categories(client)
    files = {"image": ("nails.bmp", io.BytesIO(b"fake"), "image/bmp")}
    # No client call should happen; validation rejects before the model.
    response = await client.post("/api/analyze-nails", files=files)
    assert response.status_code == 400


async def test_analyze_nails_empty_file(client):
    await seed_categories(client)
    files = {"image": ("nails.jpg", io.BytesIO(b""), "image/jpeg")}
    response = await client.post("/api/analyze-nails", files=files)
    assert response.status_code == 400


async def test_analyze_nails_missing_file(client):
    await seed_categories(client)
    response = await client.post("/api/analyze-nails")
    # FastAPI returns 422 for a missing required file field.
    assert response.status_code == 422
