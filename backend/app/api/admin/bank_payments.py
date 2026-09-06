"""Admin bank verification and payment management endpoints."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.database.connection import get_db
from app.models import (
    User, Farmer, BankDetails, Booking, ProcurementRecord,
    ProcurementCentre, Payment, CultivationRecord, Slot,
)

router = APIRouter(prefix="/api/admin", tags=["admin-bank-payments"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class BankVerifyRequest(BaseModel):
    decision: str  # "VERIFIED" or "REJECTED"
    reason: str | None = None


class BankDetailAdminResponse(BaseModel):
    bank_detail_id: str
    farmer_id: str
    farmer_name: str
    passbook_number: str
    mobile_number: str
    mandal: str
    district: str
    account_holder_name: str
    account_number_masked: str
    ifsc_code: str
    verification_status: str
    verified_at: str | None
    rejected_reason: str | None
    verified_by_username: str | None


class PaymentAdminResponse(BaseModel):
    payment_id: str
    booking_number: str
    farmer_name: str
    passbook_number: str
    crop: str
    accepted_quantity: float
    msp_per_quintal: float
    amount_payable: float
    payment_status: str
    payment_direction: str
    bank_verified: bool
    bank_account_masked: str
    transaction_reference: str | None
    payment_date: str | None
    expected_credit_date: str | None
    failure_reason: str | None
    centre_name: str
    slot_date: str


class PaymentUpdateRequest(BaseModel):
    payment_status: str | None = None
    transaction_reference: str | None = None
    expected_credit_date: str | None = None
    failure_reason: str | None = None


class PaymentDashboard(BaseModel):
    pending_payments: int
    ready_payments: int
    processing_payments: int
    credited_today: int
    failed_payments: int
    total_amount_pending: float
    total_amount_processing: float


# ── Bank Verification ─────────────────────────────────────────────────────────


@router.get("/bank-verification", response_model=list[BankDetailAdminResponse])
def list_bank_verifications(
    status: str = "PENDING_VERIFICATION",
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List bank details by verification status in admin's district."""
    district = admin.district or ""

    query = (
        db.query(BankDetails)
        .join(Farmer, BankDetails.farmer_id == Farmer.farmer_id)
        .filter(Farmer.district == district)
    )
    if status and status != "ALL":
        query = query.filter(BankDetails.verification_status == status)

    bank_details = query.order_by(BankDetails.created_at.asc()).all()
    return [_build_bank_response(bd, db) for bd in bank_details]


@router.put("/bank-verification/{bank_detail_id}")
def verify_bank_details(
    bank_detail_id: str,
    payload: BankVerifyRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Verify or reject a farmer's bank details."""
    try:
        uuid_val = UUID(bank_detail_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid bank detail ID")

    bd = db.get(BankDetails, uuid_val)
    if not bd:
        raise HTTPException(status_code=404, detail="Bank details not found")

    # Verify district scope
    farmer = db.get(Farmer, bd.farmer_id)
    if not farmer or farmer.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Not in your district")

    if payload.decision not in ("VERIFIED", "REJECTED"):
        raise HTTPException(status_code=400, detail="Decision must be VERIFIED or REJECTED")

    if payload.decision == "REJECTED" and not payload.reason:
        raise HTTPException(status_code=400, detail="Rejection requires a reason")

    now = datetime.now(timezone.utc)
    bd.verification_status = payload.decision
    bd.verified_at = now
    bd.verified_by = admin.user_id
    if payload.decision == "REJECTED":
        bd.rejected_reason = payload.reason

    db.commit()
    db.refresh(bd)
    return _build_bank_response(bd, db)


# ── Payment Dashboard ─────────────────────────────────────────────────────────


@router.get("/payments/dashboard", response_model=PaymentDashboard)
def get_payment_dashboard(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get payment summary stats for admin's district."""
    district = admin.district or ""
    today = datetime.now(timezone.utc).date()

    # Base query: payments through bookings in admin's district
    base = (
        db.query(Payment)
        .join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id)
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
    )

    pending = base.filter(Payment.payment_status == "PENDING").count()
    ready = base.filter(Payment.payment_status == "READY").count()
    processing = base.filter(Payment.payment_status == "PROCESSING").count()
    credited_today = base.filter(
        Payment.payment_status == "COMPLETED",
        func.date(Payment.payment_date) == today,
    ).count()
    failed = base.filter(Payment.payment_status == "FAILED").count()

    total_pending = db.query(
        func.coalesce(func.sum(Payment.amount_payable), 0)
    ).join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id
    ).join(Booking, ProcurementRecord.booking_id == Booking.booking_id
    ).join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district, Payment.payment_status == "PENDING"
    ).scalar()

    total_processing = db.query(
        func.coalesce(func.sum(Payment.amount_payable), 0)
    ).join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id
    ).join(Booking, ProcurementRecord.booking_id == Booking.booking_id
    ).join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district, Payment.payment_status == "PROCESSING"
    ).scalar()

    return PaymentDashboard(
        pending_payments=pending,
        ready_payments=ready,
        processing_payments=processing,
        credited_today=credited_today,
        failed_payments=failed,
        total_amount_pending=float(total_pending),
        total_amount_processing=float(total_processing),
    )


# ── Payment List ──────────────────────────────────────────────────────────────


@router.get("/payments", response_model=list[PaymentAdminResponse])
def list_payments(
    status: str | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all payments in admin's district with eligibility info."""
    district = admin.district or ""

    query = (
        db.query(Payment)
        .join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id)
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
    )
    if status:
        query = query.filter(Payment.payment_status == status)

    payments = query.order_by(Payment.created_at.desc()).all()
    return [_build_payment_response(p, db) for p in payments]


@router.put("/payments/{payment_id}", response_model=PaymentAdminResponse)
def update_payment(
    payment_id: str,
    payload: PaymentUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update payment status and details."""
    try:
        uuid_val = UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID")

    payment = db.get(Payment, uuid_val)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Verify district scope
    procurement = db.get(ProcurementRecord, payment.procurement_id)
    if procurement:
        booking = db.get(Booking, procurement.booking_id)
        if booking:
            centre = db.get(ProcurementCentre, booking.centre_id)
            if not centre or centre.district != (admin.district or ""):
                raise HTTPException(status_code=403, detail="Not in your district")

    now = datetime.now(timezone.utc)

    if payload.payment_status is not None:
        valid_statuses = ["PENDING", "READY", "PROCESSING", "COMPLETED", "FAILED"]
        if payload.payment_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

        # Check payment eligibility before marking READY
        if payload.payment_status in ("READY", "PROCESSING", "COMPLETED"):
            _check_payment_eligibility(payment, procurement, db)

        payment.payment_status = payload.payment_status
        if payload.payment_status == "COMPLETED":
            payment.payment_date = now
        elif payload.payment_status == "PROCESSING":
            payment.processed_at = now

    if payload.transaction_reference is not None:
        payment.transaction_reference = payload.transaction_reference
    if payload.expected_credit_date is not None:
        try:
            payment.expected_credit_date = datetime.fromisoformat(payload.expected_credit_date)
        except ValueError:
            payment.expected_credit_date = None
    if payload.failure_reason is not None:
        payment.failure_reason = payload.failure_reason

    db.commit()
    db.refresh(payment)
    return _build_payment_response(payment, db)


@router.post("/payments/{payment_id}/process")
def process_payment(
    payment_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Mark a READY payment as PROCESSING."""
    try:
        uuid_val = UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID")

    payment = db.get(Payment, uuid_val)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.payment_status != "READY":
        raise HTTPException(status_code=400, detail=f"Payment is {payment.payment_status}, not READY")

    # Verify district scope
    procurement = db.get(ProcurementRecord, payment.procurement_id)
    if procurement:
        booking = db.get(Booking, procurement.booking_id)
        if booking:
            centre = db.get(ProcurementCentre, booking.centre_id)
            if not centre or centre.district != (admin.district or ""):
                raise HTTPException(status_code=403, detail="Not in your district")

    now = datetime.now(timezone.utc)
    payment.payment_status = "PROCESSING"
    payment.processed_at = now
    payment.expected_credit_date = now + timedelta(days=3)

    db.commit()
    db.refresh(payment)
    return _build_payment_response(payment, db)


@router.post("/payments/{payment_id}/credit")
def credit_payment(
    payment_id: str,
    transaction_ref: str | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Mark a PROCESSING payment as COMPLETED (credited to farmer)."""
    try:
        uuid_val = UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID")

    payment = db.get(Payment, uuid_val)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.payment_status != "PROCESSING":
        raise HTTPException(status_code=400, detail=f"Payment is {payment.payment_status}, not PROCESSING")

    # Verify district scope
    procurement = db.get(ProcurementRecord, payment.procurement_id)
    if procurement:
        booking = db.get(Booking, procurement.booking_id)
        if booking:
            centre = db.get(ProcurementCentre, booking.centre_id)
            if not centre or centre.district != (admin.district or ""):
                raise HTTPException(status_code=403, detail="Not in your district")

    now = datetime.now(timezone.utc)
    payment.payment_status = "COMPLETED"
    payment.payment_date = now
    if transaction_ref:
        payment.transaction_reference = transaction_ref

    db.commit()
    db.refresh(payment)
    return _build_payment_response(payment, db)


@router.post("/payments/{payment_id}/fail")
def fail_payment(
    payment_id: str,
    reason: str = "Payment failed",
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Mark a payment as FAILED."""
    try:
        uuid_val = UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID")

    payment = db.get(Payment, uuid_val)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Verify district scope
    procurement = db.get(ProcurementRecord, payment.procurement_id)
    if procurement:
        booking = db.get(Booking, procurement.booking_id)
        if booking:
            centre = db.get(ProcurementCentre, booking.centre_id)
            if not centre or centre.district != (admin.district or ""):
                raise HTTPException(status_code=403, detail="Not in your district")

    payment.payment_status = "FAILED"
    payment.failure_reason = reason

    db.commit()
    db.refresh(payment)
    return _build_payment_response(payment, db)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _check_payment_eligibility(payment: Payment, procurement: ProcurementRecord | None, db: Session):
    """Check if payment meets eligibility requirements."""
    if not procurement:
        raise HTTPException(status_code=400, detail="Procurement record not found")

    if procurement.procurement_status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Procurement must be completed before payment")

    if procurement.quantity_accepted_quintals <= 0:
        raise HTTPException(status_code=400, detail="No accepted quantity for payment")

    # Check bank verification
    booking = db.get(Booking, procurement.booking_id)
    if booking:
        bank = db.query(BankDetails).filter(BankDetails.farmer_id == booking.farmer_id).first()
        if not bank:
            raise HTTPException(status_code=400, detail="Farmer has no bank details on file")
        if bank.verification_status != "VERIFIED":
            raise HTTPException(status_code=400, detail=f"Bank details not verified (status: {bank.verification_status})")


def _mask_account_number(account_number: str) -> str:
    """Mask account number showing only last 4 digits."""
    if len(account_number) <= 4:
        return "****"
    return "*" * (len(account_number) - 4) + account_number[-4:]


def _build_bank_response(bd: BankDetails, db: Session) -> BankDetailAdminResponse:
    farmer = db.get(Farmer, bd.farmer_id)
    verifier = db.get(User, bd.verified_by) if bd.verified_by else None

    return BankDetailAdminResponse(
        bank_detail_id=str(bd.bank_detail_id),
        farmer_id=str(bd.farmer_id),
        farmer_name=farmer.farmer_name if farmer else "",
        passbook_number=farmer.passbook_number if farmer else "",
        mobile_number=farmer.mobile_number if farmer else "",
        mandal=farmer.mandal if farmer else "",
        district=farmer.district if farmer else "",
        account_holder_name=bd.account_holder_name,
        account_number_masked=_mask_account_number(bd.account_number),
        ifsc_code=bd.ifsc_code,
        verification_status=bd.verification_status,
        verified_at=bd.verified_at.isoformat() if bd.verified_at else None,
        rejected_reason=bd.rejected_reason,
        verified_by_username=verifier.username if verifier else None,
    )


def _build_payment_response(p: Payment, db: Session) -> PaymentAdminResponse:
    procurement = db.get(ProcurementRecord, p.procurement_id)
    booking = db.get(Booking, procurement.booking_id) if procurement else None
    farmer = db.get(Farmer, booking.farmer_id) if booking else None
    cultivation = db.get(CultivationRecord, booking.cultivation_id) if booking else None
    centre = db.get(ProcurementCentre, booking.centre_id) if booking else None
    slot = db.get(Slot, booking.slot_id) if booking else None
    bank = db.query(BankDetails).filter(BankDetails.farmer_id == booking.farmer_id).first() if booking else None

    return PaymentAdminResponse(
        payment_id=str(p.payment_id),
        booking_number=booking.booking_number if booking else "",
        farmer_name=farmer.farmer_name if farmer else "",
        passbook_number=farmer.passbook_number if farmer else "",
        crop=cultivation.crop if cultivation else "",
        accepted_quantity=float(procurement.quantity_accepted_quintals) if procurement else 0,
        msp_per_quintal=float(procurement.price_per_quintal) if procurement else 0,
        amount_payable=float(p.amount_payable),
        payment_status=p.payment_status,
        payment_direction=p.payment_direction,
        bank_verified=bank.verification_status == "VERIFIED" if bank else False,
        bank_account_masked=_mask_account_number(bank.account_number) if bank else "****",
        transaction_reference=p.transaction_reference,
        payment_date=p.payment_date.isoformat() if p.payment_date else None,
        expected_credit_date=p.expected_credit_date.isoformat() if p.expected_credit_date else None,
        failure_reason=p.failure_reason,
        centre_name=centre.centre_name if centre else "",
        slot_date=str(slot.slot_date) if slot else "",
    )
