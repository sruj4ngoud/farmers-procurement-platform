"""Slots endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.connection import get_db
from app.schemas.slot import SlotResponse
from app.services.slot_service import get_all_slots, get_slot_by_id

router = APIRouter(prefix="/api/slots", tags=["slots"])


@router.get("", response_model=list[SlotResponse])
async def list_slots(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get all slots."""
    slots = get_all_slots(db, limit, offset)
    return slots


@router.get("/{slot_id}", response_model=SlotResponse)
async def get_slot(
    slot_id: str,
    db: Session = Depends(get_db),
):
    """Get slot by ID."""
    try:
        slot_uuid = UUID(slot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid slot ID format")

    slot = get_slot_by_id(db, slot_uuid)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot
