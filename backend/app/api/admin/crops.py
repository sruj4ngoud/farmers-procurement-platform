"""Admin crop management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_permissions import get_current_admin
from app.database.connection import get_db
from app.models import User, Crop
from app.schemas.admin import CropCreate, CropUpdate, CropResponse

router = APIRouter(prefix="/api/admin/crops", tags=["admin-crops"])


@router.get("", response_model=list[CropResponse])
def list_crops(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all crops (active and inactive)."""
    crops = db.query(Crop).order_by(Crop.crop_name).all()
    return [_crop_to_response(c) for c in crops]


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(
    crop_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get a single crop by ID."""
    try:
        uuid_val = UUID(crop_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid crop ID")
    crop = db.get(Crop, uuid_val)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    return _crop_to_response(crop)


@router.post("", response_model=CropResponse, status_code=201)
def create_crop(
    payload: CropCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Add a new crop."""
    existing = db.query(Crop).filter(Crop.crop_name == payload.crop_name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Crop already exists")

    crop = Crop(
        crop_name=payload.crop_name,
        crop_category=payload.crop_category,
        msp_per_quintal=payload.msp_per_quintal,
        msp_effective_date=payload.msp_effective_date,
        is_active=True,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return _crop_to_response(crop)


@router.put("/{crop_id}", response_model=CropResponse)
def update_crop(
    crop_id: str,
    payload: CropUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update a crop's details or activate/deactivate it."""
    try:
        uuid_val = UUID(crop_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid crop ID")

    crop = db.get(Crop, uuid_val)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    if payload.crop_name is not None:
        dup = db.query(Crop).filter(Crop.crop_name == payload.crop_name, Crop.crop_id != uuid_val).first()
        if dup:
            raise HTTPException(status_code=409, detail="Crop name already exists")
        crop.crop_name = payload.crop_name
    if payload.crop_category is not None:
        crop.crop_category = payload.crop_category
    if payload.msp_per_quintal is not None:
        crop.msp_per_quintal = payload.msp_per_quintal
    if payload.msp_effective_date is not None:
        crop.msp_effective_date = payload.msp_effective_date
    if payload.is_active is not None:
        crop.is_active = payload.is_active

    db.commit()
    db.refresh(crop)
    return _crop_to_response(crop)


def _crop_to_response(crop: Crop) -> CropResponse:
    return CropResponse(
        crop_id=str(crop.crop_id),
        crop_name=crop.crop_name,
        crop_category=crop.crop_category,
        is_active=crop.is_active,
        msp_per_quintal=float(crop.msp_per_quintal) if crop.msp_per_quintal else None,
        msp_effective_date=str(crop.msp_effective_date) if crop.msp_effective_date else None,
    )
