"""Booking business logic service."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.constants import CONFIRMED_BOOKING_STATUSES
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models import (
    Booking,
    CultivationRecord,
    Payment,
    ProcurementCentre,
    ProcurementRecord,
    Slot,
)
from app.schemas.booking import (
    BookingCreateRequest,
    BookingDetailResponse,
)
from app.schemas.centre import CentreResponse
from app.schemas.cultivation import CultivationResponse
from app.schemas.payment import PaymentResponse
from app.schemas.procurement import ProcurementResponse
from app.schemas.slot import SlotResponse
from app.services.notification_service import notify_booking_created
from app.services.queue_service import get_queue_position, get_queue_token_by_booking_id
from app.utils.booking_number import generate_booking_number


def _as_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def get_booking_by_id(db: Session, booking_id: UUID) -> Booking | None:
    """Get booking by booking_id."""
    return db.execute(
        select(Booking).where(Booking.booking_id == booking_id)
    ).scalar_one_or_none()


def get_all_bookings(
    db: Session, limit: int = 10, offset: int = 0
) -> list[Booking]:
    """Get all bookings with pagination."""
    return db.execute(select(Booking).limit(limit).offset(offset)).scalars().all()


def count_all_bookings(db: Session) -> int:
    """Count total bookings."""
    return (
        db.execute(select(Booking)).scalars().all().__len__()
    )


def get_bookings_by_farmer(
    db: Session, farmer_id: UUID, limit: int = 10, offset: int = 0
) -> list[Booking]:
    """Get bookings for a farmer with pagination (newest first)."""
    return (
        db.execute(
            select(Booking)
            .where(Booking.farmer_id == farmer_id)
            .order_by(Booking.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )


def count_bookings_by_farmer(db: Session, farmer_id: UUID) -> int:
    """Count bookings for a farmer."""
    return (
        db.execute(select(Booking).where(Booking.farmer_id == farmer_id))
        .scalars()
        .all().__len__()
    )


def _confirmed_quantity_for_cultivation(db: Session, cultivation_id: UUID) -> Decimal:
    """Total quantity locked in by CONFIRMED bookings for a cultivation."""
    total = db.execute(
        select(func.coalesce(func.sum(Booking.quantity_to_sell_quintals), 0)).where(
            Booking.cultivation_id == cultivation_id,
            Booking.booking_status.in_(CONFIRMED_BOOKING_STATUSES),
        )
    ).scalar_one()
    return _as_decimal(total)


def create_booking(
    db: Session,
    farmer_id: UUID,
    request: BookingCreateRequest,
) -> Booking:
    """Create a procurement booking inside a transaction.

    Concurrency approach:
      * the cultivation and slot rows are locked with SELECT ... FOR UPDATE so a
        concurrent booking cannot slip past the quantity/capacity re-checks;
      * all quantity/capacity/duplicate validation happens *after* acquiring the
        locks (i.e. re-checked inside the transaction);
      * slot.booked_farmers is incremented atomically as part of the same
        transaction and the whole unit rolls back if anything fails.
    """
    requested = _as_decimal(request.quantity_to_sell_quintals)
    if requested <= 0:
        raise BadRequestError("Quantity to sell must be greater than zero")

    cultivation = db.execute(
        select(CultivationRecord)
        .where(CultivationRecord.cultivation_id == request.cultivation_id)
        .with_for_update()
    ).scalar_one_or_none()
    if cultivation is None:
        raise NotFoundError("Cultivation not found")
    if cultivation.farmer_id != farmer_id:
        raise ForbiddenError("Cultivation does not belong to this farmer")

    slot = db.execute(
        select(Slot).where(Slot.slot_id == request.slot_id).with_for_update()
    ).scalar_one_or_none()
    if slot is None:
        raise NotFoundError("Slot not found")
    if slot.centre_id != request.centre_id:
        raise BadRequestError("Slot does not belong to the given centre")

    centre = db.execute(
        select(ProcurementCentre).where(
            ProcurementCentre.centre_id == request.centre_id
        )
    ).scalar_one_or_none()
    if centre is None:
        raise NotFoundError("Procurement centre not found")

    if not slot.is_active:
        raise BadRequestError("Slot is not available for booking")
    if slot.booked_farmers >= slot.maximum_farmers:
        raise ConflictError("Slot is full; no more farmers can be booked")

    # Quantity re-check inside the transaction (cultivation row is locked above).
    confirmed = _confirmed_quantity_for_cultivation(db, cultivation.cultivation_id)
    remaining = _as_decimal(cultivation.quantity_to_sell_quintals) - confirmed
    if requested > remaining:
        raise ConflictError(
            "Requested quantity exceeds the remaining sellable quantity "
            f"({remaining} quintals)"
        )

    # Conflicting duplicate: an active CONFIRMED booking already exists for this
    # farmer + cultivation + slot.
    duplicate = db.execute(
        select(Booking).where(
            Booking.farmer_id == farmer_id,
            Booking.cultivation_id == cultivation.cultivation_id,
            Booking.slot_id == slot.slot_id,
            Booking.booking_status.in_(CONFIRMED_BOOKING_STATUSES),
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise ConflictError(
            "A confirmed booking already exists for this cultivation and slot"
        )

    booking = Booking(
        booking_number=generate_booking_number(),
        farmer_id=farmer_id,
        cultivation_id=cultivation.cultivation_id,
        centre_id=centre.centre_id,
        slot_id=slot.slot_id,
        quantity_to_sell_quintals=requested,
        booking_status="PENDING_ADMIN_REVIEW",
    )
    db.add(booking)
    slot.booked_farmers += 1

    try:
        db.flush()
        notify_booking_created(db, booking)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(booking)
    return booking


_BOOKING_DETAIL_LOADS = (
    selectinload(Booking.cultivation),
    selectinload(Booking.centre),
    selectinload(Booking.slot),
    selectinload(Booking.queue_token),
    selectinload(Booking.procurement_record).selectinload(ProcurementRecord.payment),
)


def get_booking_with_context(db: Session, booking_id: UUID) -> Booking | None:
    """Booking eager-loaded with cultivation/centre/slot/token/procurement."""
    return db.execute(
        select(Booking)
        .options(*_BOOKING_DETAIL_LOADS)
        .where(Booking.booking_id == booking_id)
    ).scalar_one_or_none()


def build_booking_detail(db: Session, booking: Booking) -> BookingDetailResponse:
    """Serialize a booking together with its full procurement context."""
    token = get_queue_token_by_booking_id(db, booking.booking_id)
    procurement = booking.procurement_record
    payment = procurement.payment if procurement is not None else None

    token_response = None
    if token is not None:
        token_response = {
            "queue_id": token.queue_id,
            "booking_id": token.booking_id,
            "token_number": token.token_number,
            "queue_status": token.queue_status,
            "called_at": token.called_at,
            "processing_started_at": token.processing_started_at,
            "completed_at": token.completed_at,
            "created_at": token.created_at,
            "position": get_queue_position(db, booking),
        }

    payment_response = None
    if payment is not None:
        payment_response = {
            "payment_id": payment.payment_id,
            "procurement_id": payment.procurement_id,
            "amount_payable": payment.amount_payable,
            "payment_status": payment.payment_status,
            "transaction_reference": payment.transaction_reference,
            "payment_date": payment.payment_date,
            "failure_reason": payment.failure_reason,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
        }

    return BookingDetailResponse(
        booking_id=booking.booking_id,
        booking_number=booking.booking_number,
        farmer_id=booking.farmer_id,
        cultivation_id=booking.cultivation_id,
        centre_id=booking.centre_id,
        slot_id=booking.slot_id,
        quantity_to_sell_quintals=booking.quantity_to_sell_quintals,
        booking_status=booking.booking_status,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        cultivation=CultivationResponse.model_validate(booking.cultivation)
        if booking.cultivation is not None
        else None,
        centre=CentreResponse.model_validate(booking.centre)
        if booking.centre is not None
        else None,
        slot=SlotResponse.model_validate(booking.slot)
        if booking.slot is not None
        else None,
        token=token_response,
        procurement=ProcurementResponse.model_validate(procurement)
        if procurement is not None
        else None,
        payment=payment_response,
    )
