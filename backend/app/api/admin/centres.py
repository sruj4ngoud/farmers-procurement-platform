"""Admin procurement centre management endpoints."""

from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.database.connection import get_db
from app.models import User, ProcurementCentre
from app.schemas.admin import CentreCreate, CentreUpdate, CentreAdminResponse

router = APIRouter(prefix="/api/admin/centres", tags=["admin-centres"])


@router.get("", response_model=list[CentreAdminResponse])
def list_centres(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all procurement centres in admin's district."""
    district = admin.district or ""
    centres = (
        db.query(ProcurementCentre)
        .filter(ProcurementCentre.district == district)
        .order_by(ProcurementCentre.centre_name)
        .all()
    )
    return [_centre_to_response(c) for c in centres]


@router.get("/{centre_id}", response_model=CentreAdminResponse)
def get_centre(
    centre_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get a single centre in admin's district."""
    try:
        uuid_val = UUID(centre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid centre ID")

    centre = db.get(ProcurementCentre, uuid_val)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    if centre.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Centre not in your district")
    return _centre_to_response(centre)


@router.post("", response_model=CentreAdminResponse, status_code=201)
def create_centre(
    payload: CentreCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Add a new procurement centre in admin's district."""
    district = admin.district or ""

    existing = db.query(ProcurementCentre).filter(
        ProcurementCentre.centre_code == payload.centre_code
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Centre code already exists")

    centre = ProcurementCentre(
        centre_code=payload.centre_code,
        centre_name=payload.centre_name,
        agency=payload.agency,
        village=payload.village,
        mandal=payload.mandal,
        district=district,
        latitude=Decimal(str(payload.latitude)) if payload.latitude else None,
        longitude=Decimal(str(payload.longitude)) if payload.longitude else None,
        capacity=payload.capacity,
        current_status=payload.current_status,
    )
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return _centre_to_response(centre)


@router.put("/{centre_id}", response_model=CentreAdminResponse)
def update_centre(
    centre_id: str,
    payload: CentreUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update a centre in admin's district."""
    try:
        uuid_val = UUID(centre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid centre ID")

    centre = db.get(ProcurementCentre, uuid_val)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    if centre.district != (admin.district or ""):
        raise HTTPException(status_code=403, detail="Centre not in your district")

    if payload.centre_name is not None:
        centre.centre_name = payload.centre_name
    if payload.agency is not None:
        centre.agency = payload.agency
    if payload.village is not None:
        centre.village = payload.village
    if payload.mandal is not None:
        centre.mandal = payload.mandal
    if payload.latitude is not None:
        centre.latitude = Decimal(str(payload.latitude))
    if payload.longitude is not None:
        centre.longitude = Decimal(str(payload.longitude))
    if payload.capacity is not None:
        centre.capacity = payload.capacity
    if payload.current_status is not None:
        centre.current_status = payload.current_status

    db.commit()
    db.refresh(centre)
    return _centre_to_response(centre)


def _centre_to_response(c: ProcurementCentre) -> CentreAdminResponse:
    return CentreAdminResponse(
        centre_id=str(c.centre_id),
        centre_code=c.centre_code,
        centre_name=c.centre_name,
        agency=c.agency,
        village=c.village,
        mandal=c.mandal,
        district=c.district,
        latitude=float(c.latitude) if c.latitude else None,
        longitude=float(c.longitude) if c.longitude else None,
        capacity=c.capacity,
        current_status=c.current_status,
    )
