"""Stripe Checkout endpoints for deposit payments."""

import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.limiter import limiter
from src.schemas.appointment import AppointmentCreate, CheckoutSessionResponse
from src.services.email_service import send_confirmation_email
from src.services.stripe_service import (
    _extract_appointment_id,
    create_checkout_session,
    handle_checkout_completed,
    handle_checkout_expired,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/api/checkout/create-session",
    response_model=CheckoutSessionResponse,
    status_code=201,
)
@limiter.limit("10/hour")
async def create_session(
    request: Request,
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Create a Stripe Checkout Session for the €15 deposit.

    Creates the appointment in PENDING_PAYMENT status and returns
    a Stripe checkout URL for the client to complete payment.
    """
    result = await create_checkout_session(data, db)
    return CheckoutSessionResponse(
        checkout_url=result["checkout_url"],
        session_id=result["session_id"],
        appointment_id=result["appointment_id"],
    )


@router.post("/api/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Handle Stripe webhook events.

    Verifies the signature, then processes checkout.session.completed
    and checkout.session.expired events.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    session_data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await handle_checkout_completed(session_data, db)

        # Send confirmation email after successful payment
        appointment_id = _extract_appointment_id(session_data)
        if appointment_id:
            await _send_confirmation_for_appointment(appointment_id, db)

    elif event_type == "checkout.session.expired":
        await handle_checkout_expired(session_data, db)

    return {"received": True}


async def _send_confirmation_for_appointment(
    appointment_id: str, db: AsyncSession
) -> None:
    """Look up appointment details and send confirmation email."""
    from sqlalchemy import select

    from src.models.appointment import Appointment
    from src.models.design_tier import DesignTier
    from src.models.nail_type import NailType

    try:
        result = await db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()
        if not appointment:
            return

        nt_result = await db.execute(
            select(NailType).where(NailType.id == appointment.nail_type_id)
        )
        nail_type = nt_result.scalar_one_or_none()
        nail_type_name = nail_type.name if nail_type else "Nail Service"

        design_tier_name = None
        if appointment.design_tier_id:
            dt_result = await db.execute(
                select(DesignTier).where(DesignTier.id == appointment.design_tier_id)
            )
            design_tier = dt_result.scalar_one_or_none()
            design_tier_name = design_tier.name if design_tier else None

        await send_confirmation_email(
            client_email=appointment.client_email,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            nail_type_name=nail_type_name,
            design_tier_name=design_tier_name,
            quoted_price=float(appointment.quoted_price),
        )
    except Exception as e:  # noqa: BLE001
        logger.error(
            "Failed to send confirmation email for appointment %s: %s",
            appointment_id,
            e,
        )
