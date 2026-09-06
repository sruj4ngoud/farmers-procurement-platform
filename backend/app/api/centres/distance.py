"""Nearby centres endpoint using Haversine distance."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.centre import CentreWithDistanceResponse
from app.services.centre_service import get_centres_with_coordinates
from app.services.distance_service import haversine_distance
from app.services.farmer_service import get_farmer_by_passbook_number

router = APIRouter(prefix="/api/centres", tags=["centres"])


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
