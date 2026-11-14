"""Monthly sets: one-of-one designs the artist posts. Each can be booked once.

A model's state is derived from its appointments:
- available: active and no live appointment
- reserved: a PENDING_PAYMENT appointment holds it
- booked: a BOOKED or COMPLETED appointment holds it
- hidden: the admin switched it off

CANCELED and NO_SHOW appointments release the model. The partial unique index
on appointments.monthly_set_model_id is the final guarantee against double booking.
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import (
    ConflictError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from src.models.appointment import Appointment, Status
from src.models.monthly_set_model import MonthlySetModel
from src.schemas.monthly_set import (
    MonthlySetAdminResponse,
    MonthlySetPublicResponse,
    MonthlySetState,
    MonthlySetUpdate,
)
from src.services.s3_service import (
    MONTHLY_SET_PREFIX,
    delete_object,
    generate_presigned_url,
    upload_nail_image,
)

logger = logging.getLogger(__name__)

# Appointment statuses that hold a model. Must match the partial unique index.
HOLDING_STATUSES = (Status.PENDING_PAYMENT, Status.BOOKED, Status.COMPLETED)


def _holding_appointments_query():
    return select(Appointment).where(
        Appointment.monthly_set_model_id.is_not(None),
        Appointment.status.in_(HOLDING_STATUSES),
    )


async def _presign_all(keys: list[str | None]) -> list[str | None]:
    # boto3 is blocking, so sign off the event loop.
    return await asyncio.gather(
        *(asyncio.to_thread(generate_presigned_url, key) for key in keys)
    )


async def _upload(image_bytes: bytes, content_type: str) -> str:
    key = await asyncio.to_thread(
        upload_nail_image, image_bytes, content_type, MONTHLY_SET_PREFIX
    )
    if key is None:
        # Unlike client photos, the design photo is required.
        raise StorageError("Could not upload the photo. Please try again.")
    return key


def _clean_description(description: str | None) -> str | None:
    if description is None:
        return None
    description = description.strip()
    return description or None


async def _get_model(db: AsyncSession, model_id: UUID) -> MonthlySetModel:
    result = await db.execute(select(MonthlySetModel).where(MonthlySetModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise NotFoundError("Monthly set not found!")
    return model


# ── Public ──────────────────────────────────────────────────────────────────


async def list_available(db: AsyncSession) -> list[MonthlySetPublicResponse]:
    """Active models nobody holds. Taken designs disappear from the site."""
    held = _holding_appointments_query().with_only_columns(
        Appointment.monthly_set_model_id
    )
    result = await db.execute(
        select(MonthlySetModel)
        .where(MonthlySetModel.is_active, MonthlySetModel.id.not_in(held))
        .order_by(MonthlySetModel.sort_order, MonthlySetModel.created_at.desc())
    )
    models = result.scalars().all()
    urls = await _presign_all([m.image_key for m in models])
    return [
        MonthlySetPublicResponse(
            id=m.id,
            title=m.title,
            price=float(m.price),
            duration_minutes=m.duration_minutes,
            description=m.description,
            image_url=url,
        )
        for m, url in zip(models, urls)
    ]


async def get_bookable_model(
    db: AsyncSession, model_id: UUID, lock: bool = False
) -> MonthlySetModel:
    """Return the model if it can be booked right now.

    With lock=True the row is locked FOR UPDATE until the caller commits, so
    two clients booking the same design at once are processed one at a time.
    """
    query = select(MonthlySetModel).where(MonthlySetModel.id == model_id)
    if lock:
        query = query.with_for_update()
    result = await db.execute(query)
    model = result.scalar_one_or_none()
    if not model or not model.is_active:
        raise NotFoundError("This design is no longer available!")

    holder = await db.execute(
        _holding_appointments_query()
        .where(Appointment.monthly_set_model_id == model_id)
        .limit(1)
    )
    if holder.scalar_one_or_none():
        raise ConflictError("This design was just booked by someone else!")
    return model


# ── Admin ───────────────────────────────────────────────────────────────────


def _state(model: MonthlySetModel, holder: Appointment | None) -> MonthlySetState:
    if holder is not None:
        if holder.status == Status.PENDING_PAYMENT:
            return MonthlySetState.RESERVED
        return MonthlySetState.BOOKED
    if not model.is_active:
        return MonthlySetState.HIDDEN
    return MonthlySetState.AVAILABLE


async def _admin_responses(
    db: AsyncSession, models: list[MonthlySetModel]
) -> list[MonthlySetAdminResponse]:
    ids = [m.id for m in models]
    holders: dict[UUID, Appointment] = {}
    booked_ids: set[UUID] = set()
    if ids:
        result = await db.execute(
            _holding_appointments_query().where(Appointment.monthly_set_model_id.in_(ids))
        )
        holders = {a.monthly_set_model_id: a for a in result.scalars().all()}
        result = await db.execute(
            select(Appointment.monthly_set_model_id)
            .where(Appointment.monthly_set_model_id.in_(ids))
            .distinct()
        )
        booked_ids = set(result.scalars().all())

    urls = await _presign_all([m.image_key for m in models])
    responses = []
    for model, url in zip(models, urls):
        holder = holders.get(model.id)
        responses.append(
            MonthlySetAdminResponse(
                id=model.id,
                title=model.title,
                price=float(model.price),
                duration_minutes=model.duration_minutes,
                description=model.description,
                image_url=url,
                is_active=model.is_active,
                sort_order=model.sort_order,
                state=_state(model, holder),
                has_bookings=model.id in booked_ids,
                appointment_id=holder.id if holder else None,
                client_email=holder.client_email if holder else None,
                appointment_start=holder.start_time if holder else None,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
        )
    return responses


async def list_all(db: AsyncSession) -> list[MonthlySetAdminResponse]:
    result = await db.execute(
        select(MonthlySetModel).order_by(
            MonthlySetModel.sort_order, MonthlySetModel.created_at.desc()
        )
    )
    return await _admin_responses(db, list(result.scalars().all()))


async def admin_response(db: AsyncSession, model: MonthlySetModel) -> MonthlySetAdminResponse:
    return (await _admin_responses(db, [model]))[0]


async def create_model(
    db: AsyncSession,
    *,
    title: str,
    price: float,
    duration_minutes: int,
    description: str | None,
    image_bytes: bytes,
    content_type: str,
) -> MonthlySetModel:
    image_key = await _upload(image_bytes, content_type)
    model = MonthlySetModel(
        title=title.strip(),
        price=price,
        duration_minutes=duration_minutes,
        description=_clean_description(description),
        image_key=image_key,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


async def update_model(
    db: AsyncSession, model_id: UUID, data: MonthlySetUpdate
) -> MonthlySetModel:
    """Edits never touch existing bookings. Their price is locked in
    appointments.quoted_price at booking time."""
    model = await _get_model(db, model_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("title") is not None:
        changes["title"] = changes["title"].strip()
        if not changes["title"]:
            raise ValidationError("Title can't be empty!")
    if "description" in changes:
        changes["description"] = _clean_description(changes["description"])
    for key, value in changes.items():
        if value is None and key != "description":
            continue
        setattr(model, key, value)
    await db.commit()
    await db.refresh(model)
    return model


async def replace_image(
    db: AsyncSession, model_id: UUID, image_bytes: bytes, content_type: str
) -> MonthlySetModel:
    model = await _get_model(db, model_id)
    old_key = model.image_key
    model.image_key = await _upload(image_bytes, content_type)
    await db.commit()
    await db.refresh(model)
    # Only drop the old photo once the new one is saved.
    await asyncio.to_thread(delete_object, old_key)
    return model


async def delete_model(db: AsyncSession, model_id: UUID) -> None:
    """Hard delete, only for models that were never booked. Booked ones stay
    for appointment history; the admin hides them instead."""
    model = await _get_model(db, model_id)
    result = await db.execute(
        select(Appointment.id).where(Appointment.monthly_set_model_id == model_id).limit(1)
    )
    if result.scalar_one_or_none():
        raise ConflictError(
            "This design has bookings and is kept for history. Hide it instead."
        )
    image_key = model.image_key
    await db.delete(model)
    await db.commit()
    await asyncio.to_thread(delete_object, image_key)
