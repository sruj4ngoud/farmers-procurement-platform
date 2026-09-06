"""Farmer dashboard aggregation service."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.booking import BookingDetailResponse
from app.schemas.cultivation import CultivationResponse
from app.schemas.dashboard import FarmerDashboardResponse
from app.schemas.farmer import FarmerResponse
from app.schemas.land import LandRecordResponse
from app.schemas.notification import NotificationResponse
from app.services.booking_service import build_booking_detail, get_bookings_by_farmer
from app.services.cultivation_service import get_cultivations_by_farmer
from app.services.farmer_service import get_farmer_by_id, get_lands_by_farmer
from app.services.notification_service import get_unread_notifications


def get_farmer_dashboard(
    db: Session, farmer_id: UUID, booking_limit: int = 50
) -> FarmerDashboardResponse:
    """Aggregate everything a farmer needs on their dashboard."""
    farmer = get_farmer_by_id(db, farmer_id)
    if farmer is None:  # pragma: no cover - guarded by auth dependency
        raise RuntimeError("Authenticated farmer not found")

    land_records = get_lands_by_farmer(db, farmer_id)
    cultivations = get_cultivations_by_farmer(db, farmer_id, limit=100, offset=0)
    bookings = get_bookings_by_farmer(db, farmer_id, limit=booking_limit, offset=0)
    unread = get_unread_notifications(db, farmer_id, limit=100)

    booking_summaries: list[BookingDetailResponse] = [
        build_booking_detail(db, booking) for booking in bookings
    ]

    return FarmerDashboardResponse(
        farmer=FarmerResponse.model_validate(farmer),
        land_records=[LandRecordResponse.model_validate(r) for r in land_records],
        cultivations=[CultivationResponse.model_validate(c) for c in cultivations],
        bookings=booking_summaries,
        unread_notifications=len(unread),
        notifications=[NotificationResponse.model_validate(n) for n in unread],
    )
