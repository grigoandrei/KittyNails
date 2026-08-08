import io
from types import SimpleNamespace
from unittest.mock import patch

from src.schemas.nail_analysis import (
    DesignComplexityClassification,
    ExtensionsClassification,
    LengthClassification,
    NailClassification,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_parsed_message(
    classification: NailClassification | None, stop_reason: str = "end_turn"
):
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
    """Seed the nail types and design tiers the AI can classify into."""
    for name, price, dur, order in [
        ("Regular", 40.0, 90, 1),
        ("Extensions", 55.0, 150, 2),
    ]:
        await client.post(
            "/api/admin/nail-types",
            json={
                "name": name,
                "price": price,
                "duration_minutes": dur,
                "sort_order": order,
            },
        )
    for name, price, dur, order in [
        ("Simple", 0.0, 0, 1),
        ("Medium", 10.0, 0, 2),
        ("Advanced", 20.0, 30, 3),
    ]:
        await client.post(
            "/api/admin/design-tiers",
            json={
                "name": name,
                "price": price,
                "duration_minutes": dur,
                "sort_order": order,
            },
        )


def fake_image_file():
    return {"image": ("nails.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}


def make_classification(
    extensions: str = "extensions",
    extensions_confidence: float = 0.9,
    complexity: str = "complex",
    complexity_confidence: float = 0.85,
    length: str = "long",
    length_confidence: float = 0.8,
) -> NailClassification:
    """Build a NailClassification with sensible defaults."""
    return NailClassification(
        length=LengthClassification(length),
        length_confidence=length_confidence,
        design_complexity=DesignComplexityClassification(complexity),
        design_complexity_confidence=complexity_confidence,
        extensions=ExtensionsClassification(extensions),
        extensions_confidence=extensions_confidence,
        visible_details="Test nails visible.",
        uncertainties="None.",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_analyze_nails_happy_path(client):
    await seed_categories(client)
    classification = make_classification(
        extensions="extensions",
        complexity="complex",
        length="long",
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
    # Price/duration: Extensions(55) + Advanced(20) = 75, 150 + 30 = 180
    assert data["estimated_price"] == 75.0
    assert data["estimated_duration_minutes"] == 180
    assert data["confidence"] == "high"
    assert "nail_type_id" in data and "design_tier_id" in data
    assert data["length"] == "long"


async def test_analyze_nails_pricing_regular_simple(client):
    """Regular nails with minimal design → Regular + Simple pricing."""
    await seed_categories(client)
    classification = make_classification(
        extensions="natural",
        complexity="minimal",
        length="short",
    )

    with patch(
        "src.services.nail_analysis_service.get_client",
        return_value=mock_client_returning(classification),
    ):
        response = await client.post("/api/analyze-nails", files=fake_image_file())

    assert response.status_code == 200
    data = response.json()
    assert data["nail_type"] == "Regular"
    assert data["design_tier"] == "Simple"
    # Regular(40) + Simple(0) = 40, 90 + 0 = 90
    assert data["estimated_price"] == 40.0
    assert data["estimated_duration_minutes"] == 90


async def test_analyze_nails_uncertain_extensions_defaults_to_regular(client):
    """When extensions is uncertain, we default to Regular nail type."""
    await seed_categories(client)
    classification = make_classification(
        extensions="uncertain",
        complexity="medium",
        length="medium",
    )

    with patch(
        "src.services.nail_analysis_service.get_client",
        return_value=mock_client_returning(classification),
    ):
        response = await client.post("/api/analyze-nails", files=fake_image_file())

    assert response.status_code == 200
    data = response.json()
    assert data["nail_type"] == "Regular"
    assert data["design_tier"] == "Medium"
    # Regular(40) + Medium(10) = 50, 90 + 0 = 90
    assert data["estimated_price"] == 50.0
    assert data["estimated_duration_minutes"] == 90


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

    classification = make_classification(
        extensions="extensions",
        complexity="minimal",
        length="long",
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
    assert response.status_code == 422
