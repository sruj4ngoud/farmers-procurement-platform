"""Farmer-facing crop list and MSP endpoints — read from database."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Crop

router = APIRouter(prefix="/api", tags=["crops-public"])


@router.get("/crops")
def list_active_crops(db: Session = Depends(get_db)):
    """List all active crops with MSP — used by farmer portal."""
    crops = (
        db.query(Crop)
        .filter(Crop.is_active == True)
        .order_by(Crop.crop_name)
        .all()
    )
    return [
        {
            "crop_id": str(c.crop_id),
            "name": c.crop_name,
            "category": c.crop_category,
            "msp_per_quintal": float(c.msp_per_quintal) if c.msp_per_quintal else None,
        }
        for c in crops
    ]


@router.get("/crops/{crop_name}/msp")
def get_crop_msp(crop_name: str, db: Session = Depends(get_db)):
    """Get MSP for a specific crop from database."""
    crop = db.query(Crop).filter(Crop.crop_name == crop_name, Crop.is_active == True).first()
    if not crop or not crop.msp_per_quintal:
        return {"crop": crop_name, "msp": None, "message": "MSP not available for this crop"}
    return {"crop": crop_name, "msp": float(crop.msp_per_quintal), "unit": "INR per quintal"}


@router.get("/crop-categories")
def list_crop_categories(db: Session = Depends(get_db)):
    """List distinct active crop categories."""
    categories = (
        db.query(Crop.crop_category)
        .filter(Crop.is_active == True)
        .distinct()
        .order_by(Crop.crop_category)
        .all()
    )
    return [c[0] for c in categories]
