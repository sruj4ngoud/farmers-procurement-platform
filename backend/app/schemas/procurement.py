"""Procurement record response schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProcurementResponse(BaseModel):
    """Procurement record detail response."""

    model_config = ConfigDict(from_attributes=True)

    procurement_id: UUID
    booking_id: UUID
    quantity_submitted_quintals: Decimal
    quantity_accepted_quintals: Decimal
    price_per_quintal: Decimal
    procurement_status: str
    verified_by: UUID | None = None
    remarks: str | None = None
    created_at: datetime
