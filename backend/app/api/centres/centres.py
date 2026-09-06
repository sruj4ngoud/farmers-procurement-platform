"""Procurement centre endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.centre import CentreResponse, CentreWithDistanceResponse
from app.schemas.slot import SlotResponse
from app.services.centre_service import (
    get_all_centres,
    get_centre_by_id,
    get_centres_with_coordinates,
)
from app.services.distance_service import haversine_distance
from app.services.farmer_service import get_farmer_by_passbook_number
from app.services.slot_service import get_slots_by_centre

router = APIRouter(prefix="/api/centres", tags=["centres"])


@router.get("", response_model=list[CentreResponse])
async def list_centres(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get all procurement centres."""
    centres = get_all_centres(db, limit, offset)
    return centres


@router.get("/nearby", response_model=list[CentreWithDistanceResponse])
async def get_nearby_centres(
    passbook_number: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get nearby centres for a farmer.

    Uses farmer's location to calculate distance to all centres with Haversine formula.
    """
    farmer = get_farmer_by_passbook_number(db, passbook_number)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    if farmer.latitude is None or farmer.longitude is None:
        raise HTTPException(status_code=400, detail="Farmer location not available")

    centres = get_centres_with_coordinates(db)

    # Calculate distances and build response
    centres_with_distance = []
    for centre in centres:
        distance = haversine_distance(
            farmer.latitude, farmer.longitude, centre.latitude, centre.longitude
        )
        centres_with_distance.append(
            CentreWithDistanceResponse(
                **{
                    **{col: getattr(centre, col) for col in centre.__table__.columns.keys()},
                    "distance_km": distance,
                }
            )
        )

    # Sort by distance and apply pagination
    centres_with_distance.sort(key=lambda x: x.distance_km)
    paginated = centres_with_distance[offset : offset + limit]

    return paginated


@router.get("/{centre_id}", response_model=CentreResponse)
async def get_centre(
    centre_id: str,
    db: Session = Depends(get_db),
):
    """Get centre by ID."""
    try:
        centre_uuid = UUID(centre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid centre ID format")

    centre = get_centre_by_id(db, centre_uuid)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    return centre


@router.get("/{centre_id}/slots", response_model=list[SlotResponse])
async def get_centre_slots(
    centre_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get slots for a centre."""
    try:
        centre_uuid = UUID(centre_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid centre ID format")

    centre = get_centre_by_id(db, centre_uuid)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    slots = get_slots_by_centre(db, centre_uuid, limit, offset)
    return slots
