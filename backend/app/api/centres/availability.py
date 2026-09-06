"""Centre slots endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.connection import get_db
from app.schemas.slot import SlotResponse
from app.services.centre_service import get_centre_by_id
from app.services.slot_service import get_slots_by_centre

router = APIRouter(prefix="/api/centres", tags=["centres"])


@router.get("/{centre_id}/slots", response_model=list[SlotResponse])
async def get_centre_slots(
    centre_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get slots for a centre."""
    try:
        centre_uuid = UUID(centre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid centre ID format")

    centre = get_centre_by_id(db, centre_uuid)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    slots = get_slots_by_centre(db, centre_uuid, limit, offset)
    return slots
