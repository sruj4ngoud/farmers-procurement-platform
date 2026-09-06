"""Admin slot management endpoints."""

from datetime import time as dtime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.database.connection import get_db
from app.models import User, Slot, ProcurementCentre, Booking
from app.schemas.admin import SlotCreate, SlotUpdate, SlotAdminResponse

router = APIRouter(prefix="/api/admin/slots", tags=["admin-slots"])


def _parse_time(t: str) -> dtime:
    """Parse HH:MM string to time object."""
    parts = t.split(":")
    return dtime(int(parts[0]), int(parts[1]))


@router.get("", response_model=list[SlotAdminResponse])
def list_slots(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all slots for centres in admin's district."""
    district = admin.district or ""
    slots = (
        db.query(Slot)
        .join(ProcurementCentre, Slot.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .order_by(Slot.slot_date, Slot.start_time)
        .all()
    )
    return [_slot_to_response(s, db) for s in slots]


@router.get("/{slot_id}", response_model=SlotAdminResponse)
def get_slot(
    slot_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get a single slot in admin's district."""
    try:
        uuid_val = UUID(slot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid slot ID")

    slot = db.get(Slot, uuid_val)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    centre = db.get(ProcurementCentre, slot.centre_id)
    if not centre or centre.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Slot not in your district")

    return _slot_to_response(slot, db)


@router.post("", response_model=SlotAdminResponse, status_code=201)
def create_slot(
    payload: SlotCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new slot. Centre must be in admin's district."""
    district = admin.district or ""
    try:
        centre_uuid = UUID(payload.centre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid centre ID")

    centre = db.get(ProcurementCentre, centre_uuid)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    if centre.district != district:
        raise HTTPException(status_code=403, detail="Centre not in your district")

    # Check for duplicate
    existing = db.query(Slot).filter(
        Slot.centre_id == centre_uuid,
        Slot.slot_date == payload.slot_date,
        Slot.start_time == _parse_time(payload.start_time),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slot already exists for this date and time")

    slot = Slot(
        centre_id=centre_uuid,
        slot_date=payload.slot_date,
        start_time=_parse_time(payload.start_time),
        end_time=_parse_time(payload.end_time),
        maximum_farmers=payload.maximum_farmers,
        booked_farmers=0,
        is_active=payload.is_active,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return _slot_to_response(slot, db)


@router.put("/{slot_id}", response_model=SlotAdminResponse)
def update_slot(
    slot_id: str,
    payload: SlotUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update a slot. Cannot change capacity if slot has completed bookings."""
    try:
        uuid_val = UUID(slot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid slot ID")

    slot = db.get(Slot, uuid_val)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    centre = db.get(ProcurementCentre, slot.centre_id)
    if not centre or centre.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Slot not in your district")

    # Protect against destructive changes on slots with completed bookings
    completed_bookings = db.query(Booking).filter(
        Booking.slot_id == uuid_val,
        Booking.booking_status.in_(["COMPLETED", "CONFIRMED"]),
    ).count()
    if completed_bookings > 0:
        if payload.maximum_farmers is not None and payload.maximum_farmers < slot.booked_farmers:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reduce capacity below booked count ({slot.booked_farmers})"
            )

    if payload.slot_date is not None:
        slot.slot_date = payload.slot_date
    if payload.start_time is not None:
        slot.start_time = _parse_time(payload.start_time)
    if payload.end_time is not None:
        slot.end_time = _parse_time(payload.end_time)
    if payload.maximum_farmers is not None:
        slot.maximum_farmers = payload.maximum_farmers
    if payload.is_active is not None:
        slot.is_active = payload.is_active

    db.commit()
    db.refresh(slot)
    return _slot_to_response(slot, db)


def _slot_to_response(s: Slot, db: Session) -> SlotAdminResponse:
    centre = db.get(ProcurementCentre, s.centre_id)
    return SlotAdminResponse(
        slot_id=str(s.slot_id),
        centre_id=str(s.centre_id),
        centre_name=centre.centre_name if centre else None,
        slot_date=str(s.slot_date),
        start_time=s.start_time.strftime("%H:%M"),
        end_time=s.end_time.strftime("%H:%M"),
        maximum_farmers=s.maximum_farmers,
        booked_farmers=s.booked_farmers,
        is_active=s.is_active,
    )
