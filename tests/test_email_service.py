"""Tests for the email service (SES integration).

Unit tests (formatting/HTML/send logic) don't need a database.
Integration tests (appointment endpoint) use the DB via the `client` fixture.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.services.email_service import (
    _confirmation_html,
    _format_datetime_berlin,
    _reminder_html,
    send_confirmation_email,
    send_reminder_email,
)

# -- Helper data --

SAMPLE_START = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)
SAMPLE_END = datetime(2026, 8, 15, 11, 30, tzinfo=UTC)
SAMPLE_EMAIL = "client@example.com"
SAMPLE_NAIL_TYPE = "Regular"
SAMPLE_DESIGN_TIER = "Medium"
SAMPLE_PRICE = 50.00


# ============================================================
# Unit tests (no DB needed) — override the autouse DB fixture
# ============================================================


class TestFormatDatetime:
    """Pure unit tests for datetime formatting."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Override conftest's setup_database to avoid DB connection."""
        yield

    def test_format_datetime_berlin_summer(self):
        """Berlin is UTC+2 in summer (CEST)."""
        dt = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)
        result = _format_datetime_berlin(dt)
        # 10:00 UTC = 12:00 CEST
        assert "12:00" in result
        assert "August 15, 2026" in result
        assert "Saturday" in result

    def test_format_datetime_berlin_winter(self):
        """Berlin is UTC+1 in winter (CET)."""
        dt = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
        result = _format_datetime_berlin(dt)
        # 10:00 UTC = 11:00 CET
        assert "11:00" in result
        assert "January 15, 2026" in result


class TestHtmlTemplates:
    """Pure unit tests for HTML template generation."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Override conftest's setup_database to avoid DB connection."""
        yield

    def test_confirmation_html_contains_details(self):
        html = _confirmation_html(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            end_time=SAMPLE_END,
            nail_type_name=SAMPLE_NAIL_TYPE,
            design_tier_name=SAMPLE_DESIGN_TIER,
            quoted_price=SAMPLE_PRICE,
        )
        assert "Booking Confirmed" in html
        assert SAMPLE_NAIL_TYPE in html
        assert SAMPLE_DESIGN_TIER in html
        assert "€50.00" in html
        assert "KittyNails Berlin" in html
        assert "Stallschreiberstraße" in html

    def test_confirmation_html_no_design_tier(self):
        html = _confirmation_html(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            end_time=SAMPLE_END,
            nail_type_name="Japanese Manicure",
            design_tier_name=None,
            quoted_price=30.00,
        )
        assert "Japanese Manicure" in html
        assert "€30.00" in html
        assert "Japanese Manicure —" not in html

    def test_reminder_html_contains_details(self):
        html = _reminder_html(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            nail_type_name=SAMPLE_NAIL_TYPE,
            design_tier_name=SAMPLE_DESIGN_TIER,
        )
        assert "Reminder" in html
        assert "Tomorrow" in html
        assert SAMPLE_NAIL_TYPE in html
        assert SAMPLE_DESIGN_TIER in html
        assert "KittyNails Berlin" in html

    def test_reminder_html_no_design_tier(self):
        html = _reminder_html(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            nail_type_name="Japanese Manicure",
            design_tier_name=None,
        )
        assert "Japanese Manicure" in html
        assert "Japanese Manicure —" not in html


class TestSendFunctions:
    """Tests for the async send functions (mocking SES client)."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Override conftest's setup_database to avoid DB connection."""
        yield

    @patch("src.services.email_service._get_ses_client")
    async def test_send_confirmation_email_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await send_confirmation_email(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            end_time=SAMPLE_END,
            nail_type_name=SAMPLE_NAIL_TYPE,
            design_tier_name=SAMPLE_DESIGN_TIER,
            quoted_price=SAMPLE_PRICE,
        )

        assert result is True
        mock_client.send_email.assert_called_once()
        call_kwargs = mock_client.send_email.call_args[1]
        assert call_kwargs["Destination"]["ToAddresses"] == [SAMPLE_EMAIL]
        assert "Confirmed" in call_kwargs["Message"]["Subject"]["Data"]

    @patch("src.services.email_service._get_ses_client")
    async def test_send_reminder_email_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await send_reminder_email(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            nail_type_name=SAMPLE_NAIL_TYPE,
            design_tier_name=SAMPLE_DESIGN_TIER,
        )

        assert result is True
        mock_client.send_email.assert_called_once()
        call_kwargs = mock_client.send_email.call_args[1]
        assert call_kwargs["Destination"]["ToAddresses"] == [SAMPLE_EMAIL]
        assert "Reminder" in call_kwargs["Message"]["Subject"]["Data"]

    @patch("src.services.email_service._get_ses_client")
    async def test_send_email_ses_client_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.send_email.side_effect = ClientError(
            {
                "Error": {
                    "Code": "MessageRejected",
                    "Message": "Email address not verified",
                }
            },
            "SendEmail",
        )
        mock_get_client.return_value = mock_client

        result = await send_confirmation_email(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            end_time=SAMPLE_END,
            nail_type_name=SAMPLE_NAIL_TYPE,
            design_tier_name=SAMPLE_DESIGN_TIER,
            quoted_price=SAMPLE_PRICE,
        )

        assert result is False

    @patch("src.services.email_service._get_ses_client")
    async def test_send_email_unexpected_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.send_email.side_effect = RuntimeError("Network issue")
        mock_get_client.return_value = mock_client

        result = await send_confirmation_email(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            end_time=SAMPLE_END,
            nail_type_name=SAMPLE_NAIL_TYPE,
            design_tier_name=SAMPLE_DESIGN_TIER,
            quoted_price=SAMPLE_PRICE,
        )

        assert result is False

    @patch("src.services.email_service.settings")
    async def test_send_confirmation_email_disabled(self, mock_settings):
        mock_settings.SES_ENABLED = False

        result = await send_confirmation_email(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            end_time=SAMPLE_END,
            nail_type_name=SAMPLE_NAIL_TYPE,
            design_tier_name=SAMPLE_DESIGN_TIER,
            quoted_price=SAMPLE_PRICE,
        )

        assert result is False

    @patch("src.services.email_service.settings")
    async def test_send_reminder_email_disabled(self, mock_settings):
        mock_settings.SES_ENABLED = False

        result = await send_reminder_email(
            client_email=SAMPLE_EMAIL,
            start_time=SAMPLE_START,
            nail_type_name=SAMPLE_NAIL_TYPE,
            design_tier_name=SAMPLE_DESIGN_TIER,
        )

        assert result is False


# ============================================================
# Integration tests (require DB via `client` fixture)
# These are skipped when PostgreSQL is not available.
# Run with: docker compose up -d && pytest tests/test_email_service.py -k Integration
# ============================================================


class TestAppointmentEmailIntegration:
    """Tests that verify the appointment endpoint sends emails.
    Require PostgreSQL — skipped if DB is unavailable."""

    @patch("src.services.email_service._get_ses_client")
    async def test_appointment_creation_sends_confirmation_email(
        self, mock_get_client, client
    ):
        """Booking an appointment should trigger a background confirmation email."""
        mock_ses = MagicMock()
        mock_get_client.return_value = mock_ses

        nail_resp = await client.post(
            "/api/admin/nail-types",
            json={
                "name": "Regular",
                "duration_minutes": 90,
                "price": 40.00,
            },
        )
        nail_type_id = nail_resp.json()["id"]

        await client.post(
            "/api/admin/availability-rules",
            json={
                "day_of_week": 0,
                "start_time": "09:00:00",
                "end_time": "18:00:00",
            },
        )

        response = await client.post(
            "/api/appointments",
            json={
                "nail_type_id": nail_type_id,
                "client_email": "nails@example.com",
                "start_time": "2026-08-10T10:00:00+00:00",
            },
        )

        assert response.status_code == 201
        mock_ses.send_email.assert_called_once()
        call_kwargs = mock_ses.send_email.call_args[1]
        assert call_kwargs["Destination"]["ToAddresses"] == ["nails@example.com"]
        assert "Confirmed" in call_kwargs["Message"]["Subject"]["Data"]

    @patch("src.services.email_service._get_ses_client")
    async def test_appointment_creation_succeeds_even_if_email_fails(
        self, mock_get_client, client
    ):
        """Email failure should not break the booking."""
        mock_ses = MagicMock()
        mock_ses.send_email.side_effect = ClientError(
            {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
            "SendEmail",
        )
        mock_get_client.return_value = mock_ses

        nail_resp = await client.post(
            "/api/admin/nail-types",
            json={
                "name": "Regular",
                "duration_minutes": 90,
                "price": 40.00,
            },
        )
        nail_type_id = nail_resp.json()["id"]

        await client.post(
            "/api/admin/availability-rules",
            json={
                "day_of_week": 0,
                "start_time": "09:00:00",
                "end_time": "18:00:00",
            },
        )

        response = await client.post(
            "/api/appointments",
            json={
                "nail_type_id": nail_type_id,
                "client_email": "nails@example.com",
                "start_time": "2026-08-10T10:00:00+00:00",
            },
        )

        assert response.status_code == 201
        assert response.json()["status"] == "BOOKED"
