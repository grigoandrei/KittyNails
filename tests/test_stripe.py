"""Tests for the Stripe Checkout integration."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.models.appointment import Status


class TestCheckoutSession:
    """Unit tests for checkout session creation (no DB needed)."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Override conftest's setup_database to avoid DB connection."""
        yield

    @patch("src.services.stripe_service.stripe.checkout.Session.create")
    @patch("src.services.stripe_service.create_appointment")
    async def test_create_checkout_session(self, mock_create_appt, mock_stripe_create):
        from src.schemas.appointment import AppointmentCreate
        from src.services.stripe_service import create_checkout_session

        appt_id = uuid4()
        mock_appointment = MagicMock()
        mock_appointment.id = appt_id
        mock_appointment.nail_type_id = uuid4()
        mock_appointment.design_tier_id = None
        mock_appointment.stripe_session_id = None
        mock_create_appt.return_value = mock_appointment

        mock_session = MagicMock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_stripe_create.return_value = mock_session

        mock_db = MagicMock()
        mock_db.execute = MagicMock(return_value=MagicMock())
        # Make the execute call return a mock with scalar_one_or_none
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(name="Regular")
        mock_db.execute.return_value = mock_result
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Make all async methods awaitable
        async def async_execute(*args, **kwargs):
            return mock_result

        async def async_commit():
            pass

        async def async_refresh(*args):
            pass

        mock_db.execute = async_execute
        mock_db.commit = async_commit
        mock_db.refresh = async_refresh

        data = AppointmentCreate(
            nail_type_id=uuid4(),
            client_email="test@example.com",
            start_time=datetime(2026, 8, 15, 10, 0, tzinfo=UTC),
        )

        result = await create_checkout_session(data, mock_db)

        assert result["session_id"] == "cs_test_123"
        assert result["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_123"
        assert result["appointment_id"] == appt_id
        mock_create_appt.assert_called_once_with(
            data, mock_db, status=Status.PENDING_PAYMENT
        )


class TestWebhookHandlers:
    """Tests for webhook event handlers."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Override conftest's setup_database to avoid DB connection."""
        yield

    async def test_handle_checkout_completed(self):
        from src.services.stripe_service import handle_checkout_completed

        appt_id = str(uuid4())
        mock_appointment = MagicMock()
        mock_appointment.status = Status.PENDING_PAYMENT
        mock_appointment.stripe_payment_intent_id = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_appointment

        mock_db = MagicMock()

        async def async_execute(*args, **kwargs):
            return mock_result

        async def async_commit():
            pass

        mock_db.execute = async_execute
        mock_db.commit = async_commit

        session_data = {
            "metadata": {"appointment_id": appt_id},
            "payment_intent": "pi_test_abc123",
        }

        await handle_checkout_completed(session_data, mock_db)

        assert mock_appointment.status == Status.BOOKED
        assert mock_appointment.stripe_payment_intent_id == "pi_test_abc123"

    async def test_handle_checkout_completed_already_booked(self):
        """Should not change status if already BOOKED."""
        from src.services.stripe_service import handle_checkout_completed

        mock_appointment = MagicMock()
        mock_appointment.status = Status.BOOKED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_appointment

        mock_db = MagicMock()

        async def async_execute(*args, **kwargs):
            return mock_result

        async def async_commit():
            pass

        mock_db.execute = async_execute
        mock_db.commit = async_commit

        session_data = {
            "metadata": {"appointment_id": str(uuid4())},
            "payment_intent": "pi_test_xyz",
        }

        await handle_checkout_completed(session_data, mock_db)

        # Status should remain BOOKED (not modified)
        assert mock_appointment.status == Status.BOOKED

    async def test_handle_checkout_expired(self):
        from src.services.stripe_service import handle_checkout_expired

        mock_appointment = MagicMock()
        mock_appointment.status = Status.PENDING_PAYMENT

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_appointment

        mock_db = MagicMock()

        async def async_execute(*args, **kwargs):
            return mock_result

        async def async_commit():
            pass

        mock_db.execute = async_execute
        mock_db.commit = async_commit

        session_data = {"metadata": {"appointment_id": str(uuid4())}}

        await handle_checkout_expired(session_data, mock_db)

        assert mock_appointment.status == Status.CANCELED

    async def test_handle_checkout_expired_already_booked(self):
        """Should not cancel if already BOOKED (payment came through)."""
        from src.services.stripe_service import handle_checkout_expired

        mock_appointment = MagicMock()
        mock_appointment.status = Status.BOOKED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_appointment

        mock_db = MagicMock()

        async def async_execute(*args, **kwargs):
            return mock_result

        async def async_commit():
            pass

        mock_db.execute = async_execute
        mock_db.commit = async_commit

        session_data = {"metadata": {"appointment_id": str(uuid4())}}

        await handle_checkout_expired(session_data, mock_db)

        # Should NOT cancel — only cancels PENDING_PAYMENT
        assert mock_appointment.status == Status.BOOKED

    async def test_handle_checkout_completed_missing_metadata(self):
        """Should handle missing appointment_id gracefully."""
        from src.services.stripe_service import handle_checkout_completed

        mock_db = MagicMock()
        session_data = {"metadata": {}}

        # Should not raise
        await handle_checkout_completed(session_data, mock_db)

    async def test_handle_checkout_completed_stripe_object(self):
        """Regression: real Stripe payloads are StripeObjects whose nested
        metadata raises AttributeError on `.get()`. The handler must use
        item access, not `.get()`, to read the appointment_id."""
        from stripe import StripeObject

        from src.services.stripe_service import handle_checkout_completed

        appt_id = str(uuid4())

        # Build a StripeObject that mimics a real webhook payload
        metadata = StripeObject()
        metadata["appointment_id"] = appt_id
        session_data = StripeObject()
        session_data["metadata"] = metadata
        session_data["payment_intent"] = "pi_test_stripe_obj"

        # Sanity check: calling .get() on the nested StripeObject raises,
        # proving the item-access approach is necessary
        with pytest.raises(AttributeError):
            session_data.metadata.get("appointment_id")

        mock_appointment = MagicMock()
        mock_appointment.status = Status.PENDING_PAYMENT

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_appointment

        mock_db = MagicMock()

        async def async_execute(*args, **kwargs):
            return mock_result

        async def async_commit():
            pass

        mock_db.execute = async_execute
        mock_db.commit = async_commit

        await handle_checkout_completed(session_data, mock_db)

        assert mock_appointment.status == Status.BOOKED
        assert mock_appointment.stripe_payment_intent_id == "pi_test_stripe_obj"


class TestWebhookEndpoint:
    """Tests for the webhook HTTP endpoint (signature verification)."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Override conftest's setup_database to avoid DB connection."""
        yield

    @patch("src.routers.checkout.stripe.Webhook.construct_event")
    @patch("src.routers.checkout.handle_checkout_completed")
    @patch("src.routers.checkout._send_confirmation_for_appointment")
    async def test_webhook_valid_signature(
        self, mock_send_email, mock_handle, mock_construct, client
    ):
        mock_construct.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"appointment_id": str(uuid4())},
                    "payment_intent": "pi_test_123",
                }
            },
        }

        response = await client.post(
            "/api/webhooks/stripe",
            content=b'{"test": "data"}',
            headers={"stripe-signature": "t=123,v1=abc"},
        )

        assert response.status_code == 200
        assert response.json() == {"received": True}
        mock_handle.assert_called_once()

    async def test_webhook_missing_signature(self, client):
        response = await client.post(
            "/api/webhooks/stripe",
            content=b'{"test": "data"}',
        )

        assert response.status_code == 400
        assert "stripe-signature" in response.json()["detail"].lower()

    @patch("src.routers.checkout.stripe.Webhook.construct_event")
    async def test_webhook_invalid_signature(self, mock_construct, client):
        from stripe.error import SignatureVerificationError

        mock_construct.side_effect = SignatureVerificationError("bad sig", "sig_header")

        response = await client.post(
            "/api/webhooks/stripe",
            content=b'{"test": "data"}',
            headers={"stripe-signature": "t=123,v1=invalid"},
        )

        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()


class TestCheckoutEndpoint:
    """Integration test for the checkout create-session endpoint."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Override conftest's setup_database to avoid DB connection."""
        yield

    @patch("src.services.stripe_service.stripe.checkout.Session.create")
    async def test_create_session_endpoint(self, mock_stripe_create, client):
        mock_session = MagicMock()
        mock_session.id = "cs_test_456"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_456"
        mock_stripe_create.return_value = mock_session

        # Create nail type + availability first
        nail_resp = await client.post(
            "/api/admin/nail-types",
            json={"name": "Regular", "duration_minutes": 90, "price": 40.00},
        )
        nail_type_id = nail_resp.json()["id"]

        await client.post(
            "/api/admin/availability-rules",
            json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "18:00:00"},
        )

        response = await client.post(
            "/api/checkout/create-session",
            json={
                "nail_type_id": nail_type_id,
                "client_email": "pay@example.com",
                "start_time": "2026-08-10T10:00:00+00:00",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_456"
        assert data["session_id"] == "cs_test_456"
        assert "appointment_id" in data
