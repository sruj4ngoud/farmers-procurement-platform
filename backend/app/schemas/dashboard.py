"""Farmer dashboard response schemas."""

from pydantic import BaseModel

from app.schemas.booking import BookingDetailResponse
from app.schemas.cultivation import CultivationResponse
from app.schemas.farmer import FarmerResponse
from app.schemas.land import LandRecordResponse
from app.schemas.notification import NotificationResponse


class FarmerDashboardResponse(BaseModel):
    """Aggregated view of everything a farmer needs after login."""

    farmer: FarmerResponse
    land_records: list[LandRecordResponse]
    cultivations: list[CultivationResponse]
    bookings: list[BookingDetailResponse]
    unread_notifications: int
    notifications: list[NotificationResponse]
