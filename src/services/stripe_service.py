"""Stripe Checkout service for handling deposit payments."""

import logging

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.appointment import Appointment, Status
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.schemas.appointment import AppointmentCreate
from src.services.appointment_service import create_appointment

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_checkout_session(
    data: AppointmentCreate,
    db: AsyncSession,
) -> dict:
    """Create an appointment (PENDING_PAYMENT) and a Stripe Checkout Session.

    Returns a dict with checkout_url, session_id, and appointment_id.
    """
    # Create the appointment with PENDING_PAYMENT status
    appointment = await create_appointment(data, db, status=Status.PENDING_PAYMENT)

    # Look up names for the checkout description
    nt_result = await db.execute(
        select(NailType).where(NailType.id == appointment.nail_type_id)
    )
    nail_type = nt_result.scalar_one_or_none()
    service_name = nail_type.name if nail_type else "Nail Service"

    if appointment.design_tier_id:
        dt_result = await db.execute(
            select(DesignTier).where(DesignTier.id == appointment.design_tier_id)
        )
        design_tier = dt_result.scalar_one_or_none()
        if design_tier:
            service_name += f" — {design_tier.name}"

    # Create Stripe Checkout Session
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "unit_amount": settings.STRIPE_DEPOSIT_AMOUNT,
                    "product_data": {
                        "name": f"Deposit — {service_name}",
                        "description": "Non-refundable booking deposit for your nail appointment",
                    },
                },
                "quantity": 1,
            }
        ],
        metadata={"appointment_id": str(appointment.id)},
        customer_email=data.client_email,
        success_url=(
            f"{settings.FRONTEND_URL}/booking/success?session_id={{CHECKOUT_SESSION_ID}}"
        ),
        cancel_url=f"{settings.FRONTEND_URL}/booking/cancelled",
        expires_at=None,  # defaults to 24h
    )

    # Store the session ID on the appointment
    appointment.stripe_session_id = session.id
    await db.commit()
    await db.refresh(appointment)

    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "appointment_id": appointment.id,
    }


def _get_field(obj, key: str, default=None):
    """Safely read a key from either a plain dict or a Stripe StripeObject.

    StripeObject subclasses dict but its `__getattr__` raises AttributeError
    for missing attributes, so calling `.get()` on nested StripeObjects can
    fail. Item access + `in` works reliably on both types.
    """
    if obj is None:
        return default
    return obj[key] if key in obj else default  # noqa: SIM401


def _extract_appointment_id(session_data) -> str | None:
    metadata = _get_field(session_data, "metadata", {})
    return _get_field(metadata, "appointment_id")


async def handle_checkout_completed(session_data: dict, db: AsyncSession) -> None:
    """Handle a successful checkout.session.completed webhook event."""
    appointment_id = _extract_appointment_id(session_data)
    if not appointment_id:
        logger.warning(
            "Webhook checkout.session.completed missing appointment_id in metadata"
        )
        return

    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        logger.error("Appointment %s not found for checkout completion", appointment_id)
        return

    if appointment.status != Status.PENDING_PAYMENT:
        logger.info(
            "Appointment %s already in status %s, skipping",
            appointment_id,
            appointment.status.value,
        )
        return

    appointment.status = Status.BOOKED
    appointment.stripe_payment_intent_id = _get_field(session_data, "payment_intent")
    await db.commit()
    logger.info("Appointment %s confirmed (payment received)", appointment_id)


async def handle_checkout_expired(session_data: dict, db: AsyncSession) -> None:
    """Handle a checkout.session.expired webhook — cancel the pending appointment."""
    appointment_id = _extract_appointment_id(session_data)
    if not appointment_id:
        return

    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        return

    if appointment.status == Status.PENDING_PAYMENT:
        appointment.status = Status.CANCELED
        await db.commit()
        logger.info(
            "Appointment %s canceled (checkout session expired)", appointment_id
        )
