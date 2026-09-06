"""Bookings endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.core.permissions import get_current_farmer, get_optional_current_farmer
from app.database.connection import get_db
from app.schemas.booking import BookingCreateRequest, BookingDetailResponse, BookingResponse
from app.schemas.queue import QueueTokenResponse
from app.services.booking_service import (
    build_booking_detail,
    create_booking,
    get_all_bookings,
    get_booking_by_id,
)
from app.services.queue_service import (
    create_queue_token,
    get_queue_token_by_booking_id,
)


router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get all bookings."""
    bookings = get_all_bookings(db, limit, offset)
    return bookings


@router.post(
    "", response_model=BookingResponse, status_code=status.HTTP_201_CREATED
)
async def post_create_booking(
    payload: BookingCreateRequest,
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
) -> BookingResponse:
    """Create a booking for the authenticated farmer.

    Validates ownership, the centre/slot relationship, slot availability, the
    remaining cultivation quantity, and conflicting duplicate bookings inside a
    transaction with row locks to prevent overbooking.
    """
    booking = create_booking(db, farmer.farmer_id, payload)
    return booking


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: str,
    farmer=Depends(get_optional_current_farmer),
    db: Session = Depends(get_db),
) -> BookingDetailResponse:
    """Get a booking by id with the full procurement context.

    If the caller authenticates, ownership is enforced (403 for another farmer).
    Without a token the public Phase 4 read behaviour is preserved, so existing
    regression tests keep passing.
    """
    try:
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

    booking = get_booking_by_id(db, booking_uuid)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if farmer is not None and booking.farmer_id != farmer.farmer_id:
        raise ForbiddenError("Booking does not belong to this farmer")

    return build_booking_detail(db, booking)


@router.post(
    "/{booking_id}/token", response_model=QueueTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_generate_token(
    booking_id: str,
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
) -> QueueTokenResponse:
    """Generate a single queue token for the farmer's booking.

    One token per booking; the token number is the next sequential number for the
    booking's slot queue. A notification is raised once the token is created.
    """
    try:
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

    booking = get_booking_by_id(db, booking_uuid)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.farmer_id != farmer.farmer_id:
        raise ForbiddenError("Booking does not belong to this farmer")

    query_token = create_queue_token(db, booking)
    db.commit()

    from app.services.notification_service import notify_token_generated
    from app.services.queue_service import get_queue_position

    notify_token_generated(db, booking, query_token.token_number, commit=True)
    db.refresh(query_token)
    position = get_queue_position(db, booking)
    return QueueTokenResponse(
        queue_id=query_token.queue_id,
        booking_id=query_token.booking_id,
        token_number=query_token.token_number,
        queue_status=query_token.queue_status,
        called_at=query_token.called_at,
        processing_started_at=query_token.processing_started_at,
        completed_at=query_token.completed_at,
        created_at=query_token.created_at,
        position=position,
    )
