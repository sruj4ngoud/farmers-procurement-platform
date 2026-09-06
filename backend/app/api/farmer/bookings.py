"""Farmer bookings endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.booking import BookingResponse
from app.services.booking_service import get_bookings_by_farmer
from app.services.farmer_service import get_farmer_by_passbook_number

router = APIRouter(prefix="/api/farmers", tags=["farmers"])


@router.get("/{passbook_number}/bookings", response_model=list[BookingResponse])
async def get_farmer_bookings(
    passbook_number: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get bookings for a farmer."""
    farmer = get_farmer_by_passbook_number(db, passbook_number)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    bookings = get_bookings_by_farmer(db, farmer.farmer_id, limit, offset)
    return bookings
