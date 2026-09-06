"""Farmer cultivation records endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.permissions import get_current_farmer
from app.database.connection import get_db
from app.schemas.cultivation import CultivationCreateRequest, CultivationResponse
from app.services.cultivation_service import (
    create_cultivation,
    get_cultivations_by_farmer,
)
from app.services.farmer_service import get_farmer_by_passbook_number

# Public router (no auth) — backward compatible
public_router = APIRouter(prefix="/api/farmers", tags=["farmers"])

# Authenticated router
router = APIRouter(prefix="/api/farmer", tags=["farmer"])


@public_router.get(
    "/{passbook_number}/cultivations", response_model=list[CultivationResponse]
)
async def get_farmer_cultivations(
    passbook_number: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get cultivation records for a farmer (public, by passbook number)."""
    farmer = get_farmer_by_passbook_number(db, passbook_number)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return get_cultivations_by_farmer(db, farmer.farmer_id, limit, offset)


@router.get("/cultivations", response_model=list[CultivationResponse])
def list_my_cultivations(
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Get all cultivation records for the authenticated farmer."""
    return get_cultivations_by_farmer(db, farmer.farmer_id, limit, offset)


@router.post("/cultivations", response_model=CultivationResponse, status_code=201)
def post_create_cultivation(
    payload: CultivationCreateRequest,
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Create a new cultivation record for the authenticated farmer.

    Validates land capacity: total cultivated area must not exceed registered land.
    """
    cultivation = create_cultivation(
        db=db,
        farmer_id=farmer.farmer_id,
        crop=payload.crop,
        season=payload.season,
        cultivated_area_acres=payload.cultivated_area_acres,
        quantity_produced_quintals=payload.quantity_produced_quintals,
    )
    return cultivation
