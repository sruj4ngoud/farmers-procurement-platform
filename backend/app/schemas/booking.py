"""Booking response schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.centre import CentreResponse
from app.schemas.cultivation import CultivationResponse
from app.schemas.payment import PaymentResponse
from app.schemas.procurement import ProcurementResponse
from app.schemas.queue import QueueTokenResponse
from app.schemas.slot import SlotResponse


class BookingResponse(BaseModel):
    """Booking detail response."""

    model_config = ConfigDict(from_attributes=True)

    booking_id: UUID
    booking_number: str
    farmer_id: UUID
    cultivation_id: UUID
    centre_id: UUID
    slot_id: UUID
    quantity_to_sell_quintals: Decimal
    booking_status: str
    created_at: datetime
    updated_at: datetime


class BookingCreateRequest(BaseModel):
    """Request body to create a new procurement booking."""

    cultivation_id: UUID
    centre_id: UUID
    slot_id: UUID
    quantity_to_sell_quintals: Decimal = Field(gt=0, le=10_000_000)


class BookingDetailResponse(BookingResponse):
    """Booking detail enriched with the full procurement context.

    Returned by GET /api/bookings/{booking_id} and included in the farmer
    dashboard so a farmer can follow a booking end to end.
    """

    cultivation: CultivationResponse | None = None
    centre: CentreResponse | None = None
    slot: SlotResponse | None = None
    token: QueueTokenResponse | None = None
    procurement: ProcurementResponse | None = None
    payment: PaymentResponse | None = None
