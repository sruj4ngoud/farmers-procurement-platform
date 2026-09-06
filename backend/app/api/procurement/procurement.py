"""Procurement endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.core.permissions import get_optional_current_farmer
from app.database.connection import get_db
from app.schemas.procurement import ProcurementResponse
from app.services.booking_service import get_booking_by_id
from app.services.procurement_service import get_procurement_by_booking_id

router = APIRouter(prefix="/api/procurement", tags=["procurement"])


@router.get("/{booking_id}", response_model=ProcurementResponse)
async def get_procurement_by_booking(
    booking_id: str,
    farmer=Depends(get_optional_current_farmer),
    db: Session = Depends(get_db),
):
    """Get procurement record for a booking.

    Authenticated callers may only view their own booking's procurement
    (403 otherwise). Unauthenticated access preserves the public Phase 4
    behaviour.
    """
    try:
        booking_uuid = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

    booking = get_booking_by_id(db, booking_uuid)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if farmer is not None and booking.farmer_id != farmer.farmer_id:
        raise ForbiddenError("Procurement record does not belong to this farmer")

    procurement = get_procurement_by_booking_id(db, booking_uuid)
    if not procurement:
        raise HTTPException(
            status_code=404,
            detail="Procurement record not found for this booking",
        )
    return procurement
