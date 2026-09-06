"""Admin reports, issues, audit logs, and ML insights endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.database.connection import get_db
from app.models import (
    User, Farmer, Booking, ProcurementRecord, ProcurementCentre,
    Payment, Slot, Crop, CultivationRecord, QueueToken, Issue, AuditLog,
)

router = APIRouter(prefix="/api/admin", tags=["admin-reports"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class ReportItem(BaseModel):
    label: str
    value: int | float
    extra: str | None = None


class IssueCreate(BaseModel):
    issue_type: str
    severity: str = "MEDIUM"
    entity_type: str
    entity_id: str
    description: str


class IssueUpdate(BaseModel):
    status: str | None = None
    resolution_comment: str | None = None


class IssueResponse(BaseModel):
    issue_id: str
    issue_type: str
    severity: str
    entity_type: str
    entity_id: str
    district: str
    description: str
    status: str
    created_at: str
    resolved_at: str | None
    resolved_by_username: str | None
    resolution_comment: str | None


class AuditLogResponse(BaseModel):
    log_id: str
    username: str | None
    action: str
    entity_type: str
    entity_id: str
    old_value: str | None
    new_value: str | None
    description: str | None
    created_at: str


class MLInsightItem(BaseModel):
    centre_name: str
    current_queue: int
    predicted_congestion: str
    predicted_wait_minutes: int
    confidence: float | None


class AdminDashboardFinal(BaseModel):
    district: str
    total_farmers: int
    total_bookings: int
    pending_reviews: int
    auto_accepted: int
    active_queues: int
    total_centres: int
    pending_procurement: int
    pending_payment: float
    alerts: list[dict]
    ml_insights: list[MLInsightItem]


# ── Reports ───────────────────────────────────────────────────────────────────


@router.get("/reports/farmers")
def report_farmers(
    mandal: str | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Farmer report by mandal."""
    district = admin.district or ""
    query = db.query(Farmer).filter(Farmer.district == district)
    if mandal:
        query = query.filter(Farmer.mandal == mandal)

    farmers = query.all()
    by_mandal = {}
    for f in farmers:
        m = f.mandal
        if m not in by_mandal:
            by_mandal[m] = {"count": 0, "total_land": 0}
        by_mandal[m]["count"] += 1
        by_mandal[m]["total_land"] += float(f.total_land_acres)

    return {
        "total": len(farmers),
        "by_mandal": [{"mandal": k, "count": v["count"], "total_land_acres": round(v["total_land"], 2)} for k, v in sorted(by_mandal.items())],
    }


@router.get("/reports/crops")
def report_crops(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Crop usage report for district."""
    district = admin.district or ""

    crops_used = (
        db.query(CultivationRecord.crop, func.count(CultivationRecord.cultivation_id))
        .join(Farmer, CultivationRecord.farmer_id == Farmer.farmer_id)
        .filter(Farmer.district == district)
        .group_by(CultivationRecord.crop)
        .order_by(desc(func.count(CultivationRecord.cultivation_id)))
        .all()
    )

    return {
        "total_cultivations": sum(c[1] for c in crops_used),
        "by_crop": [{"crop": c[0], "count": c[1]} for c in crops_used],
    }


@router.get("/reports/centres")
def report_centres(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Centre utilization report."""
    district = admin.district or ""

    centres = db.query(ProcurementCentre).filter(ProcurementCentre.district == district).all()
    result = []
    for c in centres:
        total_bookings = db.query(func.count(Booking.booking_id)).filter(Booking.centre_id == c.centre_id).scalar()
        active_bookings = db.query(func.count(Booking.booking_id)).filter(
            Booking.centre_id == c.centre_id, Booking.booking_status.in_(["PENDING_ADMIN_REVIEW", "ACCEPTED", "AUTO_ACCEPTED", "CONFIRMED"])
        ).scalar()
        result.append({
            "centre_name": c.centre_name,
            "status": c.current_status,
            "capacity": c.capacity,
            "total_bookings": total_bookings,
            "active_bookings": active_bookings,
        })

    return {"centres": result}


@router.get("/reports/bookings")
def report_bookings(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Booking status report."""
    district = admin.district or ""

    statuses = (
        db.query(Booking.booking_status, func.count(Booking.booking_id))
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .group_by(Booking.booking_status)
        .all()
    )

    return {
        "total": sum(s[1] for s in statuses),
        "by_status": [{"status": s[0], "count": s[1]} for s in statuses],
    }


@router.get("/reports/payments")
def report_payments(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Payment summary report."""
    district = admin.district or ""

    statuses = (
        db.query(Payment.payment_status, func.count(Payment.payment_id), func.coalesce(func.sum(Payment.amount_payable), 0))
        .join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id)
        .join(Booking, ProcurementRecord.booking_id == Booking.booking_id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(ProcurementCentre.district == district)
        .group_by(Payment.payment_status)
        .all()
    )

    return {
        "by_status": [{"status": s[0], "count": s[1], "total_amount": float(s[2])} for s in statuses],
    }


# ── Issues ────────────────────────────────────────────────────────────────────


@router.get("/issues", response_model=list[IssueResponse])
def list_issues(
    status: str | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List issues in admin's district."""
    district = admin.district or ""
    query = db.query(Issue).filter(Issue.district == district)
    if status:
        query = query.filter(Issue.status == status)
    issues = query.order_by(Issue.created_at.desc()).all()
    return [_build_issue_response(i, db) for i in issues]


@router.post("/issues", response_model=IssueResponse, status_code=201)
def create_issue(
    payload: IssueCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new issue."""
    issue = Issue(
        issue_type=payload.issue_type,
        severity=payload.severity,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        district=admin.district or "",
        description=payload.description,
        status="OPEN",
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    _log_audit(db, admin.user_id, "CREATE_ISSUE", "issue", str(issue.issue_id), None, payload.issue_type)
    return _build_issue_response(issue, db)


@router.put("/issues/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: str,
    payload: IssueUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update issue status and resolution."""
    try:
        uuid_val = UUID(issue_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid issue ID")

    issue = db.get(Issue, uuid_val)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Not in your district")

    old_status = issue.status
    if payload.status is not None:
        issue.status = payload.status
        if payload.status == "RESOLVED":
            issue.resolved_at = datetime.now(timezone.utc)
            issue.resolved_by = admin.user_id
    if payload.resolution_comment is not None:
        issue.resolution_comment = payload.resolution_comment

    _log_audit(db, admin.user_id, "UPDATE_ISSUE", "issue", issue_id, old_status, issue.status)
    db.commit()
    db.refresh(issue)
    return _build_issue_response(issue, db)


# ── Audit Logs ────────────────────────────────────────────────────────────────


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List recent audit logs."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return [_build_audit_response(l, db) for l in logs]


# ── ML Insights ───────────────────────────────────────────────────────────────


@router.get("/ml-insights", response_model=list[MLInsightItem])
def get_ml_insights(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get ML predictions for centres in admin's district."""
    district = admin.district or ""

    centres = db.query(ProcurementCentre).filter(ProcurementCentre.district == district).all()
    result = []

    for centre in centres:
        # Get current queue count
        queue_count = (
            db.query(func.count(QueueToken.queue_id))
            .join(Booking, QueueToken.booking_id == Booking.booking_id)
            .filter(Booking.centre_id == centre.centre_id)
            .filter(QueueToken.queue_status.in_(["WAITING", "CALLED", "PROCESSING"]))
            .scalar()
        )

        # Simple ML prediction based on queue count
        if queue_count <= 3:
            congestion = "LOW"
            wait = queue_count * 15
        elif queue_count <= 8:
            congestion = "MODERATE"
            wait = queue_count * 20
        else:
            congestion = "HIGH"
            wait = queue_count * 25

        result.append(MLInsightItem(
            centre_name=centre.centre_name,
            current_queue=queue_count,
            predicted_congestion=congestion,
            predicted_wait_minutes=wait,
            confidence=0.85 if queue_count > 0 else None,
        ))

    return result


# ── Enhanced Dashboard ────────────────────────────────────────────────────────


@router.get("/dashboard-final", response_model=AdminDashboardFinal)
def get_final_dashboard(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Final comprehensive admin dashboard."""
    district = admin.district or ""

    # Counts
    total_farmers = db.query(func.count(Farmer.farmer_id)).filter(Farmer.district == district).scalar()
    total_centres = db.query(func.count(ProcurementCentre.centre_id)).filter(ProcurementCentre.district == district).scalar()
    total_bookings = db.query(func.count(Booking.booking_id)).join(
        ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district).scalar()
    pending_reviews = db.query(func.count(Booking.booking_id)).join(
        ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district, Booking.booking_status == "PENDING_ADMIN_REVIEW").scalar()
    auto_accepted = db.query(func.count(Booking.booking_id)).join(
        ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district, Booking.booking_status == "AUTO_ACCEPTED").scalar()

    active_queues = db.query(func.count(QueueToken.queue_id)).join(
        Booking, QueueToken.booking_id == Booking.booking_id
    ).join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district, QueueToken.queue_status.in_(["WAITING", "CALLED", "PROCESSING"])).scalar()

    pending_procurement = db.query(func.count(ProcurementRecord.procurement_id)).join(
        Booking, ProcurementRecord.booking_id == Booking.booking_id
    ).join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district, ProcurementRecord.procurement_status.in_(["PENDING", "PROCESSING"])).scalar()

    pending_payment = db.query(
        func.coalesce(func.sum(Payment.amount_payable), 0)
    ).join(ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id
    ).join(Booking, ProcurementRecord.booking_id == Booking.booking_id
    ).join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district, Payment.payment_status.in_(["PENDING", "READY"])).scalar()

    # Alerts
    alerts = []
    if pending_reviews > 0:
        alerts.append({"type": "warning", "message": f"{pending_reviews} booking(s) pending review"})
    if auto_accepted > 0:
        alerts.append({"type": "info", "message": f"{auto_accepted} booking(s) auto-accepted"})
    if active_queues > 5:
        alerts.append({"type": "warning", "message": f"{active_queues} farmers in active queues"})

    failed_payments = db.query(func.count(Payment.payment_id)).join(
        ProcurementRecord, Payment.procurement_id == ProcurementRecord.procurement_id
    ).join(Booking, ProcurementRecord.booking_id == Booking.booking_id
    ).join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id
    ).filter(ProcurementCentre.district == district, Payment.payment_status == "FAILED").scalar()
    if failed_payments > 0:
        alerts.append({"type": "error", "message": f"{failed_payments} failed payment(s)"})

    # ML insights
    ml_insights = get_ml_insights(admin=admin, db=db)

    return AdminDashboardFinal(
        district=district,
        total_farmers=total_farmers,
        total_bookings=total_bookings,
        pending_reviews=pending_reviews,
        auto_accepted=auto_accepted,
        active_queues=active_queues,
        total_centres=total_centres,
        pending_procurement=pending_procurement,
        pending_payment=float(pending_payment),
        alerts=alerts,
        ml_insights=ml_insights[:5],
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _log_audit(db: Session, user_id, action, entity_type, entity_id, old_value=None, new_value=None, description=None):
    """Create an audit log entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        description=description,
    )
    db.add(log)


def _build_issue_response(i: Issue, db: Session) -> IssueResponse:
    resolver = db.get(User, i.resolved_by) if i.resolved_by else None
    return IssueResponse(
        issue_id=str(i.issue_id),
        issue_type=i.issue_type,
        severity=i.severity,
        entity_type=i.entity_type,
        entity_id=i.entity_id,
        district=i.district,
        description=i.description,
        status=i.status,
        created_at=i.created_at.isoformat() if i.created_at else "",
        resolved_at=i.resolved_at.isoformat() if i.resolved_at else None,
        resolved_by_username=resolver.username if resolver else None,
        resolution_comment=i.resolution_comment,
    )


def _build_audit_response(l: AuditLog, db: Session) -> AuditLogResponse:
    user = db.get(User, l.user_id) if l.user_id else None
    return AuditLogResponse(
        log_id=str(l.log_id),
        username=user.username if user else None,
        action=l.action,
        entity_type=l.entity_type,
        entity_id=l.entity_id,
        old_value=l.old_value,
        new_value=l.new_value,
        description=l.description,
        created_at=l.created_at.isoformat() if l.created_at else "",
    )
