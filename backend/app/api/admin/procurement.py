"""Admin procurement management endpoints."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.database.connection import get_db
from app.models import (
    User, Booking, ProcurementRecord, ProcurementCentre, Payment,
)

router = APIRouter(prefix="/api/admin/procurement", tags=["admin-procurement"])


class ProcurementUpdateRequest(BaseModel):
    quantity_submitted_quintals: float | None = None
    quantity_accepted_quintals: float | None = None
    price_per_quintal: float | None = None
    procurement_status: str | None = None
    remarks: str | None = None


class ProcurementDetail(BaseModel):
    procurement_id: str
    booking_id: str
    booking_number: str
    farmer_name: str
    passbook_number: str
    crop: str
    declared_quantity: float
    submitted_quantity: float
    accepted_quantity: float
    price_per_quintal: float
    quantity_difference: float
    quantity_mismatch: bool
    procurement_status: str
    remarks: str | None
    verified_by: str | None
    centre_name: str
    slot_date: str
    payment_status: str | None
    payment_amount: float | None


@router.get("/pending", response_model=list[ProcurementDetail])
def list_pending_procurements(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all procurements needing attention in admin's district."""
    district = admin.district or ""

    procurements = (
        db.query(ProcurementRecord)
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(ProcurementRecord.procurement_status.in_(["PENDING", "PROCESSING"]))
        .order_by(ProcurementRecord.created_at.asc())
        .all()
    )

    return [_build_procurement_detail(p, db) for p in procurements]


@router.get("/all", response_model=list[ProcurementDetail])
def list_all_procurements(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all procurements in admin's district."""
    district = admin.district or ""

    procurements = (
        db.query(ProcurementRecord)
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .order_by(ProcurementRecord.created_at.desc())
        .all()
    )

    return [_build_procurement_detail(p, db) for p in procurements]


@router.get("/{booking_id}", response_model=ProcurementDetail)
def get_procurement_detail(
    booking_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get procurement detail for a specific booking."""
    try:
        uuid_val = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID")

    procurement = db.query(ProcurementRecord).filter(
        ProcurementRecord.booking_id == uuid_val
    ).first()
    if not procurement:
        raise HTTPException(status_code=404, detail="Procurement record not found")

    # Verify district scope
    booking = db.get(Booking, uuid_val)
    if booking:
        centre = db.get(ProcurementCentre, booking.centre_id)
        if not centre or centre.district != (admin.district or ""):
            raise HTTPException(status_code=403, detail="Not in your district")

    return _build_procurement_detail(procurement, db)


@router.put("/{booking_id}", response_model=ProcurementDetail)
def update_procurement(
    booking_id: str,
    payload: ProcurementUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update procurement record (quantity, price, status, remarks)."""
    try:
        uuid_val = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID")

    procurement = db.query(ProcurementRecord).filter(
        ProcurementRecord.booking_id == uuid_val
    ).first()
    if not procurement:
        raise HTTPException(status_code=404, detail="Procurement record not found")

    # Verify district scope
    booking = db.get(Booking, uuid_val)
    if booking:
        centre = db.get(ProcurementCentre, booking.centre_id)
        if not centre or centre.district != (admin.district or ""):
            raise HTTPException(status_code=403, detail="Not in your district")

    if payload.quantity_submitted_quintals is not None:
        procurement.quantity_submitted_quintals = Decimal(str(payload.quantity_submitted_quintals))
    if payload.quantity_accepted_quintals is not None:
        procurement.quantity_accepted_quintals = Decimal(str(payload.quantity_accepted_quintals))
    if payload.price_per_quintal is not None:
        procurement.price_per_quintal = Decimal(str(payload.price_per_quintal))
    if payload.procurement_status is not None:
        procurement.procurement_status = payload.procurement_status
    if payload.remarks is not None:
        procurement.remarks = payload.remarks

    procurement.verified_by = admin.user_id

    # If completing procurement, update payment if it exists
    if payload.procurement_status == "COMPLETED" and procurement.payment:
        amount = procurement.quantity_accepted_quintals * procurement.price_per_quintal
        procurement.payment.amount_payable = amount

    db.commit()
    db.refresh(procurement)
    return _build_procurement_detail(procurement, db)


@router.post("/{booking_id}/complete")
def complete_procurement(
    booking_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Mark procurement as completed and calculate final payment."""
    try:
        uuid_val = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID")

    procurement = db.query(ProcurementRecord).filter(
        ProcurementRecord.booking_id == uuid_val
    ).first()
    if not procurement:
        raise HTTPException(status_code=404, detail="Procurement record not found")

    # Verify district scope
    booking = db.get(Booking, uuid_val)
    if booking:
        centre = db.get(ProcurementCentre, booking.centre_id)
        if not centre or centre.district != (admin.district or ""):
            raise HTTPException(status_code=403, detail="Not in your district")

    procurement.procurement_status = "COMPLETED"
    procurement.verified_by = admin.user_id

    # Update payment
    if procurement.payment:
        amount = procurement.quantity_accepted_quintals * procurement.price_per_quintal
        procurement.payment.amount_payable = amount

    # Update booking status
    if booking:
        booking.booking_status = "COMPLETED"

    db.commit()
    db.refresh(procurement)
    return _build_procurement_detail(procurement, db)


def _build_procurement_detail(p: ProcurementRecord, db: Session) -> ProcurementDetail:
    """Build a ProcurementDetail from a ProcurementRecord."""
    booking = db.get(Booking, p.booking_id)
    from app.models import Farmer, CultivationRecord, Slot
    farmer = db.get(Farmer, booking.farmer_id) if booking else None
    cultivation = db.get(CultivationRecord, booking.cultivation_id) if booking else None
    slot = db.get(Slot, booking.slot_id) if booking else None
    centre = db.get(ProcurementCentre, booking.centre_id) if booking else None
    verifier = db.get(User, p.verified_by) if p.verified_by else None

    declared = float(booking.quantity_to_sell_quintals) if booking else 0
    submitted = float(p.quantity_submitted_quintals)
    accepted = float(p.quantity_accepted_quintals)
    diff = round(submitted - accepted, 2)

    return ProcurementDetail(
        procurement_id=str(p.procurement_id),
        booking_id=str(p.booking_id),
        booking_number=booking.booking_number if booking else "",
        farmer_name=farmer.farmer_name if farmer else "",
        passbook_number=farmer.passbook_number if farmer else "",
        crop=cultivation.crop if cultivation else "",
        declared_quantity=declared,
        submitted_quantity=submitted,
        accepted_quantity=accepted,
        price_per_quintal=float(p.price_per_quintal),
        quantity_difference=diff,
        quantity_mismatch=abs(diff) > 0.01,
        procurement_status=p.procurement_status,
        remarks=p.remarks,
        verified_by=verifier.username if verifier else None,
        centre_name=centre.centre_name if centre else "",
        slot_date=str(slot.slot_date) if slot else "",
        payment_status=p.payment.payment_status if p.payment else None,
        payment_amount=float(p.payment.amount_payable) if p.payment else None,
    )
