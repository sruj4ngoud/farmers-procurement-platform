"""Farmer workspace endpoints that require JWT authentication."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import get_current_farmer
from app.database.connection import get_db
from app.schemas.cultivation import QuantityToSellUpdateRequest
from app.schemas.dashboard import FarmerDashboardResponse
from app.services.cultivation_service import update_quantity_to_sell
from app.services.dashboard_service import get_farmer_dashboard

router = APIRouter(prefix="/api/farmer", tags=["farmer"])


@router.get("/dashboard", response_model=FarmerDashboardResponse)
def get_dashboard(
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
) -> FarmerDashboardResponse:
    """Authenticated farmer dashboard.

    Returns the farmer's profile, land records, cultivations, active/recent
    bookings (with queue/procurement/payment context), and unread notifications.
    """
    return get_farmer_dashboard(db, farmer.farmer_id)


@router.put("/cultivations/{cultivation_id}/quantity-to-sell")
def put_quantity_to_sell(
    cultivation_id: UUID,
    payload: QuantityToSellUpdateRequest,
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Set how much of a produced crop the farmer wants to sell.

    Cannot be reduced below the quantity already confirmed/booked in CONFIRMED
    bookings, and must not exceed the quantity actually produced.
    """
    cultivation = update_quantity_to_sell(
        db, cultivation_id, farmer.farmer_id, payload.quantity_to_sell_quintals
    )
    return {
        "cultivation_id": str(cultivation.cultivation_id),
        "crop": cultivation.crop,
        "quantity_produced_quintals": cultivation.quantity_produced_quintals,
        "quantity_to_sell_quintals": cultivation.quantity_to_sell_quintals,
    }
