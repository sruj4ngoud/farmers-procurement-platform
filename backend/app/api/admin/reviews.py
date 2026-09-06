"""Admin booking review endpoints: accept/reject with comment, 24h auto-accept."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.core.constants import CONFIRMED_BOOKING_STATUSES
from app.database.connection import get_db
from app.models import (
    User, Booking, ProcurementCentre, Slot, Farmer,
    CultivationRecord, Notification,
)
from app.services.notification_service import notify_booking_created

router = APIRouter(prefix="/api/admin/reviews", tags=["admin-reviews"])

REVIEW_DEADLINE_HOURS = 24


# ── Schemas ───────────────────────────────────────────────────────────────────


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(ACCEPT|REJECT)$")
    comment: str | None = None


class BookingReviewItem(BaseModel):
    booking_id: str
    booking_number: str
    farmer_id: str
    farmer_name: str
    passbook_number: str
    mobile_number: str
    village: str
    mandal: str
    district: str
    total_land_acres: float
    crop: str
    cultivated_area_acres: float
    quantity_to_sell_quintals: float
    centre_name: str
    centre_mandal: str
    slot_date: str
    slot_start_time: str
    slot_end_time: str
    slot_booked_farmers: int
    slot_maximum_farmers: int
    booking_status: str
    created_at: str
    review_deadline: str
    remaining_hours: float
    reviewed_at: str | None
    admin_comment: str | None
    reviewed_by_username: str | None


# ── Pending reviews list ─────────────────────────────────────────────────────


@router.get("/pending", response_model=list[BookingReviewItem])
def list_pending_reviews(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all bookings pending admin review in the admin's district."""
    district = admin.district or ""
    now = datetime.now(timezone.utc)

    bookings = (
        db.query(Booking)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(Booking.booking_status == "PENDING_ADMIN_REVIEW")
        .order_by(Booking.created_at.asc())
        .all()
    )

    return [_build_review_item(b, db, now) for b in bookings]


@router.get("/all", response_model=list[BookingReviewItem])
def list_all_reviews(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all bookings in admin's district (all statuses)."""
    district = admin.district or ""
    now = datetime.now(timezone.utc)

    bookings = (
        db.query(Booking)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return [_build_review_item(b, db, now) for b in bookings]


# ── Accept / Reject ───────────────────────────────────────────────────────────


@router.put("/{booking_id}/review", response_model=BookingReviewItem)
def review_booking(
    booking_id: str,
    payload: ReviewDecisionRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Accept or reject a pending booking. Reject requires a comment."""
    try:
        uuid_val = UUID(booking_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid booking ID")

    booking = db.get(Booking, uuid_val)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Verify district scope
    centre = db.get(ProcurementCentre, booking.centre_id)
    if not centre or centre.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Booking not in your district")

    if booking.booking_status != "PENDING_ADMIN_REVIEW":
        raise HTTPException(
            status_code=400,
            detail=f"Booking is already {booking.booking_status}",
        )

    now = datetime.now(timezone.utc)

    if payload.decision == "REJECT":
        if not payload.comment or not payload.comment.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection requires a comment explaining the reason",
            )
        booking.booking_status = "REJECTED"
        booking.admin_comment = payload.comment.strip()
        booking.reviewed_by = admin.user_id
        booking.reviewed_at = now

        # Notify farmer
        _notify_farmer(db, booking, f"Your booking {booking.booking_number} has been rejected. Reason: {payload.comment.strip()}")

    elif payload.decision == "ACCEPT":
        # Check slot capacity before accepting
        slot = db.get(Slot, booking.slot_id)
        if slot and slot.booked_farmers >= slot.maximum_farmers:
            raise HTTPException(
                status_code=400,
                detail="Cannot accept: slot is at full capacity",
            )

        booking.booking_status = "ACCEPTED"
        booking.admin_comment = payload.comment or None
        booking.reviewed_by = admin.user_id
        booking.reviewed_at = now

        # Notify farmer
        _notify_farmer(db, booking, f"Your booking {booking.booking_number} has been accepted.")

    db.commit()
    db.refresh(booking)
    return _build_review_item(booking, db, now)


# ── 24-hour auto-accept ──────────────────────────────────────────────────────


@router.post("/auto-accept")
def process_auto_accept(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Process all overdue bookings (created > 24h ago, still PENDING_ADMIN_REVIEW).

    This can be called manually or by a cron job.
    """
    now = datetime.now(timezone.utc)
    deadline = now - timedelta(hours=REVIEW_DEADLINE_HOURS)

    overdue = (
        db.query(Booking)
        .filter(Booking.booking_status == "PENDING_ADMIN_REVIEW")
        .filter(Booking.created_at <= deadline)
        .all()
    )

    count = 0
    for booking in overdue:
        # Check slot capacity
        slot = db.get(Slot, booking.slot_id)
        if slot and slot.booked_farmers >= slot.maximum_farmers:
            continue  # Skip if slot full — will remain pending

        booking.booking_status = "AUTO_ACCEPTED"
        booking.auto_accepted_at = now
        booking.admin_comment = "Auto-accepted: no admin review within 24 hours"
        booking.reviewed_at = now

        _notify_farmer(
            db, booking,
            f"Your booking {booking.booking_number} was automatically accepted "
            f"because it was not reviewed within 24 hours."
        )
        count += 1

    db.commit()
    return {"auto_accepted": count, "processed_at": now.isoformat()}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _build_review_item(b: Booking, db: Session, now: datetime) -> BookingReviewItem:
    """Build a BookingReviewItem from a Booking with all related data."""
    farmer = db.get(Farmer, b.farmer_id)
    cultivation = db.get(CultivationRecord, b.cultivation_id)
    centre = db.get(ProcurementCentre, b.centre_id)
    slot = db.get(Slot, b.slot_id)
    reviewer = db.get(User, b.reviewed_by) if b.reviewed_by else None

    # Calculate review deadline
    created = b.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    deadline = (created + timedelta(hours=REVIEW_DEADLINE_HOURS)) if created else now
    remaining = max(0, (deadline - now).total_seconds() / 3600)

    return BookingReviewItem(
        booking_id=str(b.booking_id),
        booking_number=b.booking_number,
        farmer_id=str(b.farmer_id),
        farmer_name=farmer.farmer_name if farmer else "",
        passbook_number=farmer.passbook_number if farmer else "",
        mobile_number=farmer.mobile_number if farmer else "",
        village=farmer.village if farmer else "",
        mandal=farmer.mandal if farmer else "",
        district=farmer.district if farmer else "",
        total_land_acres=float(farmer.total_land_acres) if farmer else 0,
        crop=cultivation.crop if cultivation else "",
        cultivated_area_acres=float(cultivation.cultivated_area_acres) if cultivation else 0,
        quantity_to_sell_quintals=float(b.quantity_to_sell_quintals),
        centre_name=centre.centre_name if centre else "",
        centre_mandal=centre.mandal if centre else "",
        slot_date=str(slot.slot_date) if slot else "",
        slot_start_time=slot.start_time.strftime("%H:%M") if slot else "",
        slot_end_time=slot.end_time.strftime("%H:%M") if slot else "",
        slot_booked_farmers=slot.booked_farmers if slot else 0,
        slot_maximum_farmers=slot.maximum_farmers if slot else 0,
        booking_status=b.booking_status,
        created_at=b.created_at.isoformat() if b.created_at else "",
        review_deadline=deadline.isoformat(),
        remaining_hours=round(remaining, 1),
        reviewed_at=b.reviewed_at.isoformat() if b.reviewed_at else None,
        admin_comment=b.admin_comment,
        reviewed_by_username=reviewer.username if reviewer else None,
    )


def _notify_farmer(db: Session, booking: Booking, message: str):
    """Create a notification for the farmer about a booking decision."""
    notification = Notification(
        farmer_id=booking.farmer_id,
        booking_id=booking.booking_id,
        notification_type="BOOKING_REVIEW",
        title="Booking Review Update",
        message=message,
        is_read=False,
    )
    db.add(notification)
