"""Admin API endpoints: login, dashboard, mandals, and district-scoped data."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.database.connection import get_db
from app.models import (
    User, Farmer, ProcurementCentre, Booking, Slot,
    CultivationRecord, ProcurementRecord, Payment, QueueToken,
    District, Mandal,
)
from app.schemas.admin import (
    AdminLoginRequest, AdminLoginResponse, AdminDashboardResponse,
    MandalOverviewItem, MandalDetailResponse,
)
from app.services.admin_auth_service import authenticate_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Auth ──────────────────────────────────────────────────────────────────────


@router.post("/auth/login", response_model=AdminLoginResponse)
def post_admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    """Authenticate an admin user with username + password."""
    user, token, expires_in = authenticate_admin(db, payload.username, payload.password)
    return AdminLoginResponse(
        access_token=token,
        token_type="bearer",
        admin_id=str(user.user_id),
        username=user.username,
        district=user.district or "",
        admin_name=user.username,
        expires_in_seconds=expires_in,
    )


# ── Rich Dashboard (district-scoped) ─────────────────────────────────────────


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return rich aggregate statistics for the admin's district."""
    district = admin.district or ""
    today = date.today()

    # Total farmers in district
    total_farmers = (
        db.query(func.count(Farmer.farmer_id))
        .filter(Farmer.district == district)
        .scalar()
    )

    # Active centres in district
    active_centres = (
        db.query(func.count(ProcurementCentre.centre_id))
        .filter(ProcurementCentre.district == district)
        .filter(ProcurementCentre.current_status.in_(["ACTIVE", "LIMITED"]))
        .scalar()
    )

    total_centres = (
        db.query(func.count(ProcurementCentre.centre_id))
        .filter(ProcurementCentre.district == district)
        .scalar()
    )

    # Total bookings in district
    total_bookings = (
        db.query(func.count(Booking.booking_id))
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .scalar()
    )

    # Active (confirmed) bookings
    active_bookings = (
        db.query(func.count(Booking.booking_id))
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(Booking.booking_status == "CONFIRMED")
        .scalar()
    )

    # Today's bookings
    today_bookings = (
        db.query(func.count(Booking.booking_id))
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(func.date(Booking.created_at) == today)
        .scalar()
    )

    # Farmers in queue (WAITING or CALLED)
    farmers_in_queue = (
        db.query(func.count(QueueToken.queue_id))
        .join(Booking, QueueToken.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(QueueToken.queue_status.in_(["WAITING", "CALLED", "PROCESSING"]))
        .scalar()
    )

    # Pending reviews (bookings awaiting procurement)
    pending_reviews = (
        db.query(func.count(Booking.booking_id))
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(Booking.booking_status == "CONFIRMED")
        .filter(~Booking.booking_id.in_(
            db.query(ProcurementRecord.booking_id)
        ))
        .scalar()
    )

    # Today's procurement completed
    today_procurement = (
        db.query(func.count(ProcurementRecord.procurement_id))
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(ProcurementRecord.procurement_status == "COMPLETED")
        .filter(func.date(ProcurementRecord.created_at) == today)
        .scalar()
    )

    # Payments processing (PENDING or PROCESSING)
    payments_processing = (
        db.query(func.count(Payment.payment_id))
        .join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id)
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .filter(Payment.payment_status.in_(["PENDING", "PROCESSING"]))
        .scalar()
    )

    # Total slots in district
    total_slots = (
        db.query(func.count(Slot.slot_id))
        .join(ProcurementCentre, Slot.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .scalar()
    )

    return AdminDashboardResponse(
        district=district,
        total_farmers=total_farmers,
        active_bookings=active_bookings,
        pending_reviews=pending_reviews,
        today_bookings=today_bookings,
        farmers_in_queue=farmers_in_queue,
        active_centres=active_centres,
        today_procurement=today_procurement,
        payments_processing=payments_processing,
        total_centres=total_centres,
        total_slots=total_slots,
        total_bookings=total_bookings,
    )


# ── Mandal Overview (district-scoped) ────────────────────────────────────────


@router.get("/mandals", response_model=list[MandalOverviewItem])
def list_district_mandals(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all mandals in the admin's district with aggregate stats."""
    district = admin.district or ""

    # Get all mandals in this district
    mandals = (
        db.query(Mandal)
        .join(District, Mandal.district_id == District.district_id)
        .filter(District.name == district)
        .order_by(Mandal.name)
        .all()
    )

    result = []
    for mandal in mandals:
        mandal_name = mandal.name

        # Farmers in this mandal + district
        farmers_count = (
            db.query(func.count(Farmer.farmer_id))
            .filter(Farmer.district == district, Farmer.mandal == mandal_name)
            .scalar()
        )

        # Bookings through centres in this mandal
        bookings_count = (
            db.query(func.count(Booking.booking_id))
            .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
            .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
            .scalar()
        )

        # Active queue in this mandal
        active_queue = (
            db.query(func.count(QueueToken.queue_id))
            .join(Booking, QueueToken.booking_id == Booking.booking_id)
            .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
            .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
            .filter(QueueToken.queue_status.in_(["WAITING", "CALLED", "PROCESSING"]))
            .scalar()
        )

        # Procurement completed in this mandal
        procurement_completed = (
            db.query(func.count(ProcurementRecord.procurement_id))
            .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
            .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
            .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
            .filter(ProcurementRecord.procurement_status == "COMPLETED")
            .scalar()
        )

        # Payments pending in this mandal
        payments_pending = (
            db.query(func.count(Payment.payment_id))
            .join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id)
            .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
            .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
            .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
            .filter(Payment.payment_status.in_(["PENDING", "PROCESSING"]))
            .scalar()
        )

        result.append(MandalOverviewItem(
            mandal_id=str(mandal.mandal_id),
            mandal_name=mandal_name,
            farmers=farmers_count,
            bookings=bookings_count,
            active_queue=active_queue,
            procurement_completed=procurement_completed,
            payments_pending=payments_pending,
        ))

    return result


@router.get("/mandals/{mandal_id}", response_model=MandalDetailResponse)
def get_mandal_detail(
    mandal_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get detailed info for a specific mandal (must be in admin's district)."""
    from uuid import UUID as UUIDType

    try:
        mandal_uuid = UUIDType(mandal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mandal ID")

    mandal = db.get(Mandal, mandal_uuid)
    if mandal is None:
        raise HTTPException(status_code=404, detail="Mandal not found")

    # Verify mandal belongs to admin's district
    district_obj = db.get(District, mandal.district_id)
    if district_obj is None or district_obj.name != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Access denied: mandal not in your district")

    district = admin.district or ""
    mandal_name = mandal.name

    # Counts
    farmers = (
        db.query(func.count(Farmer.farmer_id))
        .filter(Farmer.district == district, Farmer.mandal == mandal_name)
        .scalar()
    )
    centres = (
        db.query(func.count(ProcurementCentre.centre_id))
        .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
        .scalar()
    )
    bookings = (
        db.query(func.count(Booking.booking_id))
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
        .scalar()
    )
    active_queue = (
        db.query(func.count(QueueToken.queue_id))
        .join(Booking, QueueToken.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
        .filter(QueueToken.queue_status.in_(["WAITING", "CALLED", "PROCESSING"]))
        .scalar()
    )
    procurement_completed = (
        db.query(func.count(ProcurementRecord.procurement_id))
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
        .filter(ProcurementRecord.procurement_status == "COMPLETED")
        .scalar()
    )
    payments_pending = (
        db.query(func.count(Payment.payment_id))
        .join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id)
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
        .filter(Payment.payment_status.in_(["PENDING", "PROCESSING"]))
        .scalar()
    )

    # Recent bookings in this mandal
    recent = (
        db.query(Booking)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district, ProcurementCentre.mandal == mandal_name)
        .order_by(Booking.created_at.desc())
        .limit(10)
        .all()
    )
    recent_bookings = [
        {
            "booking_number": b.booking_number,
            "quantity": float(b.quantity_to_sell_quintals),
            "status": b.booking_status,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in recent
    ]

    return MandalDetailResponse(
        mandal_id=str(mandal.mandal_id),
        mandal_name=mandal_name,
        district=district,
        farmers=farmers,
        centres=centres,
        bookings=bookings,
        active_queue=active_queue,
        procurement_completed=procurement_completed,
        payments_pending=payments_pending,
        recent_bookings=recent_bookings,
    )


# ── Farmers (district-scoped) ────────────────────────────────────────────────


@router.get("/farmers")
def list_district_farmers(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all farmers in the admin's district."""
    district = admin.district or ""
    farmers = (
        db.query(Farmer)
        .filter(Farmer.district == district)
        .order_by(Farmer.farmer_name)
        .all()
    )
    return [
        {
            "farmer_id": str(f.farmer_id),
            "farmer_name": f.farmer_name,
            "passbook_number": f.passbook_number,
            "mobile_number": f.mobile_number,
            "village": f.village,
            "mandal": f.mandal,
            "district": f.district,
            "total_land_acres": float(f.total_land_acres),
        }
        for f in farmers
    ]


# ── Centres (district-scoped) ────────────────────────────────────────────────


@router.get("/centres")
def list_district_centres(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all procurement centres in the admin's district."""
    district = admin.district or ""
    centres = (
        db.query(ProcurementCentre)
        .filter(ProcurementCentre.district == district)
        .order_by(ProcurementCentre.centre_name)
        .all()
    )
    return [
        {
            "centre_id": str(c.centre_id),
            "centre_code": c.centre_code,
            "centre_name": c.centre_name,
            "agency": c.agency,
            "village": c.village,
            "mandal": c.mandal,
            "district": c.district,
            "capacity": c.capacity,
            "current_status": c.current_status,
        }
        for c in centres
    ]


# ── Bookings (district-scoped) ───────────────────────────────────────────────


@router.get("/bookings")
def list_district_bookings(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all bookings in the admin's district (through centres)."""
    district = admin.district or ""
    bookings = (
        db.query(Booking)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return [
        {
            "booking_id": str(b.booking_id),
            "booking_number": b.booking_number,
            "farmer_id": str(b.farmer_id),
            "centre_id": str(b.centre_id),
            "slot_id": str(b.slot_id),
            "quantity_to_sell_quintals": float(b.quantity_to_sell_quintals),
            "booking_status": b.booking_status,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in bookings
    ]


# ── District info helper ─────────────────────────────────────────────────────


@router.get("/district-info")
def get_district_info(
    admin: User = Depends(get_current_admin),
):
    """Return the admin's own district info."""
    return {
        "admin_id": str(admin.user_id),
        "username": admin.username,
        "district": admin.district,
        "role": admin.role,
        "is_active": admin.is_active,
    }
