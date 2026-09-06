"""Queue endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.core.permissions import get_optional_current_farmer
from app.database.connection import get_db
from app.schemas.queue import QueueTokenResponse
from app.services.booking_service import get_booking_by_id
from app.services.queue_service import get_queue_position, get_queue_token_by_booking_id

router = APIRouter(prefix="/api/queue", tags=["queue"])


def _serialize_queue_token(db: Session, booking) -> dict:
    """Return the queue token (with computed position) for a booking."""
    token = get_queue_token_by_booking_id(db, booking.booking_id)
    if token is None:
        return None
    return {
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


@router.get("/{booking_id}", response_model=QueueTokenResponse)
async def get_queue_status(
    booking_id: str,
    farmer=Depends(get_optional_current_farmer),
    db: Session = Depends(get_db),
):
    """Get queue token status for a booking with a computed queue position.

    Authenticated callers may only access their own booking's queue
    (403 otherwise). Unauthenticated access keeps the public Phase 4 behaviour.
    """
    try:
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

    booking = get_booking_by_id(db, booking_uuid)
    if booking is None:
        raise HTTPException(
            status_code=404, detail="Queue token not found for this booking"
        )

    if farmer is not None and booking.farmer_id != farmer.farmer_id:
        raise ForbiddenError("Queue token does not belong to this farmer")

    token_data = _serialize_queue_token(db, booking)
    if token_data is None:
        raise HTTPException(
            status_code=404, detail="Queue token not found for this booking"
        )
    return token_data
