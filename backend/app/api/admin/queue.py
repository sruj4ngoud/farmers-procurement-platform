"""Admin queue management endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.core.constants import ACTIVE_QUEUE_STATUSES
from app.database.connection import get_db
from app.models import (
    User, Booking, QueueToken, ProcurementCentre, Slot, Farmer, CultivationRecord,
)

router = APIRouter(prefix="/api/admin/queue", tags=["admin-queue"])

VALID_TRANSITIONS = {
    "WAITING": ["CALLED", "SKIPPED", "CANCELLED"],
    "CALLED": ["PROCESSING", "SKIPPED", "CANCELLED"],
    "PROCESSING": ["COMPLETED", "SKIPPED", "CANCELLED"],
}


class TokenTransitionRequest(BaseModel):
    new_status: str


class QueueSlotOverview(BaseModel):
    slot_id: str
    centre_id: str
    centre_name: str
    slot_date: str
    start_time: str
    end_time: str
    current_token: int | None
    waiting: int
    called: int
    processing: int
    completed: int
    total_tokens: int


class QueueTokenDetail(BaseModel):
    queue_id: str
    booking_id: str
    booking_number: str
    farmer_name: str
    passbook_number: str
    crop: str
    quantity: float
    token_number: int
    queue_status: str
    called_at: str | None
    processing_started_at: str | None
    completed_at: str | None


@router.get("/overview", response_model=list[QueueSlotOverview])
def get_queue_overview(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get queue overview grouped by slot for admin's district."""
    district = admin.district or ""

    # Get all slots in district that have queue tokens
    slots_with_tokens = (
        db.query(Slot)
        .join(ProcurementCentre, Slot.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(
            db.query(QueueToken.queue_id)
            .filter(QueueToken.booking_id == Booking.booking_id, Booking.slot_id == Slot.slot_id)
            .correlate(Slot)
            .exists()
        )
        .order_by(Slot.slot_date.desc(), Slot.start_time)
        .all()
    )

    result = []
    for slot in slots_with_tokens:
        centre = db.get(ProcurementCentre, slot.centre_id)

        # Count tokens by status for this slot
        counts = dict(
            db.query(QueueToken.queue_status, func.count(QueueToken.queue_id))
            .join(Booking, Booking.booking_id == QueueToken.booking_id)
            .filter(Booking.slot_id == slot.slot_id)
            .group_by(QueueToken.queue_status)
            .all()
        )

        # Current token = highest CALLED or PROCESSING token number
        current_token = (
            db.query(func.max(QueueToken.token_number))
            .join(Booking, Booking.booking_id == QueueToken.booking_id)
            .filter(
                Booking.slot_id == slot.slot_id,
                QueueToken.queue_status.in_(["CALLED", "PROCESSING"]),
            )
            .scalar()
        )

        result.append(QueueSlotOverview(
            slot_id=str(slot.slot_id),
            centre_id=str(slot.centre_id),
            centre_name=centre.centre_name if centre else "",
            slot_date=str(slot.slot_date),
            start_time=slot.start_time.strftime("%H:%M"),
            end_time=slot.end_time.strftime("%H:%M"),
            current_token=current_token,
            waiting=counts.get("WAITING", 0),
            called=counts.get("CALLED", 0),
            processing=counts.get("PROCESSING", 0),
            completed=counts.get("COMPLETED", 0),
            total_tokens=sum(counts.values()),
        ))

    return result


@router.get("/slot/{slot_id}/tokens", response_model=list[QueueTokenDetail])
def get_slot_tokens(
    slot_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get all queue tokens for a specific slot."""
    try:
        slot_uuid = UUID(slot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid slot ID")

    slot = db.get(Slot, slot_uuid)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    centre = db.get(ProcurementCentre, slot.centre_id)
    if not centre or centre.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Slot not in your district")

    tokens = (
        db.query(QueueToken)
        .join(Booking, Booking.booking_id == QueueToken.booking_id)
        .filter(Booking.slot_id == slot_uuid)
        .order_by(QueueToken.token_number)
        .all()
    )

    result = []
    for t in tokens:
        booking = db.get(Booking, t.booking_id)
        farmer = db.get(Farmer, booking.farmer_id) if booking else None
        cultivation = db.get(CultivationRecord, booking.cultivation_id) if booking else None
        result.append(QueueTokenDetail(
            queue_id=str(t.queue_id),
            booking_id=str(t.booking_id),
            booking_number=booking.booking_number if booking else "",
            farmer_name=farmer.farmer_name if farmer else "",
            passbook_number=farmer.passbook_number if farmer else "",
            crop=cultivation.crop if cultivation else "",
            quantity=float(booking.quantity_to_sell_quintals) if booking else 0,
            token_number=t.token_number,
            queue_status=t.queue_status,
            called_at=t.called_at.isoformat() if t.called_at else None,
            processing_started_at=t.processing_started_at.isoformat() if t.processing_started_at else None,
            completed_at=t.completed_at.isoformat() if t.completed_at else None,
        ))

    return result


@router.put("/tokens/{token_id}/transition")
def transition_token(
    token_id: str,
    payload: TokenTransitionRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Transition a queue token to a new status."""
    try:
        token_uuid = UUID(token_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token ID")

    token = db.get(QueueToken, token_uuid)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Verify district scope
    booking = db.get(Booking, token.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    centre = db.get(ProcurementCentre, booking.centre_id)
    if not centre or centre.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Token not in your district")

    # Validate transition
    valid_next = VALID_TRANSITIONS.get(token.queue_status, [])
    if payload.new_status not in valid_next:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {token.queue_status} to {payload.new_status}. "
                   f"Valid transitions: {valid_next}",
        )

    now = datetime.now(timezone.utc)
    token.queue_status = payload.new_status

    if payload.new_status == "CALLED":
        token.called_at = now
    elif payload.new_status == "PROCESSING":
        token.processing_started_at = now
    elif payload.new_status == "COMPLETED":
        token.completed_at = now

    db.commit()
    db.refresh(token)

    return {
        "queue_id": str(token.queue_id),
        "token_number": token.token_number,
        "queue_status": token.queue_status,
        "called_at": token.called_at.isoformat() if token.called_at else None,
        "processing_started_at": token.processing_started_at.isoformat() if token.processing_started_at else None,
        "completed_at": token.completed_at.isoformat() if token.completed_at else None,
    }


@router.post("/slot/{slot_id}/call-next")
def call_next_token(
    slot_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Call the next WAITING token in the slot queue."""
    try:
        slot_uuid = UUID(slot_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid slot ID")

    slot = db.get(Slot, slot_uuid)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    centre = db.get(ProcurementCentre, slot.centre_id)
    if not centre or centre.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Slot not in your district")

    # Find the next WAITING token (lowest token_number)
    next_token = (
        db.query(QueueToken)
        .join(Booking, Booking.booking_id == QueueToken.booking_id)
        .filter(
            Booking.slot_id == slot_uuid,
            QueueToken.queue_status == "WAITING",
        )
        .order_by(QueueToken.token_number)
        .first()
    )

    if not next_token:
        raise HTTPException(status_code=404, detail="No waiting tokens in this slot")

    now = datetime.now(timezone.utc)
    next_token.queue_status = "CALLED"
    next_token.called_at = now
    db.commit()
    db.refresh(next_token)

    return {
        "queue_id": str(next_token.queue_id),
        "token_number": next_token.token_number,
        "queue_status": next_token.queue_status,
        "called_at": next_token.called_at.isoformat(),
    }
