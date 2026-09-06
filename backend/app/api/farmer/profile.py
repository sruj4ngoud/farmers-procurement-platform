"""Farmer profile endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.farmer import FarmerResponse
from app.services.farmer_service import get_farmer_by_passbook_number

router = APIRouter(prefix="/api/farmers", tags=["farmers"])


@router.get("/{passbook_number}", response_model=FarmerResponse)
async def get_farmer(
    passbook_number: str,
    db: Session = Depends(get_db),
):
    """Get farmer by passbook number."""
    farmer = get_farmer_by_passbook_number(db, passbook_number)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return farmer
