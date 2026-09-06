"""Queue token business logic service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import ACTIVE_QUEUE_STATUSES
from app.core.exceptions import ConflictError
from app.models import Booking, QueueToken


def get_queue_token_by_booking_id(db: Session, booking_id: UUID) -> QueueToken | None:
    """Get queue token by booking_id."""
    return db.execute(
        select(QueueToken).where(QueueToken.booking_id == booking_id)
    ).scalar_one_or_none()


def get_queue_token_by_id(db: Session, queue_id: UUID) -> QueueToken | None:
    """Get queue token by queue_id."""
    return db.execute(
        select(QueueToken).where(QueueToken.queue_id == queue_id)
    ).scalar_one_or_none()


def _next_token_number(db: Session, slot_id: UUID) -> int:
    """Next token number for the queue of a given slot (1-based, sequential)."""
    max_number = db.execute(
        select(func.max(QueueToken.token_number))
        .join(Booking, Booking.booking_id == QueueToken.booking_id)
        .where(Booking.slot_id == slot_id)
    ).scalar_one()
    return 1 if max_number is None else int(max_number) + 1


def create_queue_token(db: Session, booking: Booking) -> QueueToken:
    """Create a single WAITING queue token for a booking.

    Rules enforced:
      * one token per booking (DB unique constraint + pre-check)
      * token numbers are unique within the slot's queue
    """
    existing = get_queue_token_by_booking_id(db, booking.booking_id)
    if existing is not None:
        raise ConflictError("A queue token already exists for this booking")

    token_number = _next_token_number(db, booking.slot_id)
    queue_token = QueueToken(
        booking_id=booking.booking_id,
        token_number=token_number,
        queue_status="WAITING",
    )
    db.add(queue_token)
    return queue_token


def get_queue_position(db: Session, booking: Booking) -> int | None:
    """Dynamically compute the 1-based position of a booking's token.

    Position is the number of still-active tokens (WAITING/CALLED/PROCESSING)
    with a token number up to and including this booking's token within the same
    slot queue. Returns None when the booking has no token or its token has left
    the active queue (e.g. COMPLETED, CANCELLED, SKIPPED).
    """
    token = get_queue_token_by_booking_id(db, booking.booking_id)
    if token is None:
        return None
    if token.queue_status not in ACTIVE_QUEUE_STATUSES:
        return None

    position = db.execute(
        select(func.count())
        .select_from(QueueToken)
        .join(Booking, Booking.booking_id == QueueToken.booking_id)
        .where(
            Booking.slot_id == booking.slot_id,
            QueueToken.queue_status.in_(ACTIVE_QUEUE_STATUSES),
            QueueToken.token_number <= token.token_number,
        )
    ).scalar_one()
    return int(position)
