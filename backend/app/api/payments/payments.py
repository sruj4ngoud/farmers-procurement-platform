"""Payments endpoints - Government to Farmer payments."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.core.permissions import get_optional_current_farmer
from app.database.connection import get_db
from app.schemas.payment import PaymentResponse
from app.services.booking_service import get_booking_by_id
from app.services.payment_service import get_payment_by_procurement_id
from app.services.procurement_service import get_procurement_by_booking_id

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("/{booking_id}", response_model=PaymentResponse)
async def get_payment_for_booking(
    booking_id: str,
    farmer=Depends(get_optional_current_farmer),
    db: Session = Depends(get_db),
):
    """Get government payment details for a booking.

    Payments always flow Government -> Farmer; the farmer never pays.

    Authenticated callers may only view their own booking's payment (403
    otherwise). Unauthenticated access preserves the public Phase 4 behaviour.
    """
    try:
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

    booking = get_booking_by_id(db, booking_uuid)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if farmer is not None and booking.farmer_id != farmer.farmer_id:
        raise ForbiddenError("Payment record does not belong to this farmer")

    # Get procurement record for this booking
    procurement = get_procurement_by_booking_id(db, booking_uuid)
    if not procurement:
        raise HTTPException(
            status_code=404,
            detail="Procurement record not found for this booking",
        )

    # Get payment for this procurement
    payment = get_payment_by_procurement_id(db, procurement.procurement_id)
    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment record not found for this booking",
        )

    # The direction is explicit on the response schema: Government -> Farmer.
    return payment
