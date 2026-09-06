"""Slot response schemas."""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SlotResponse(BaseModel):
    """Slot detail response."""

    model_config = ConfigDict(from_attributes=True)

    slot_id: UUID
    centre_id: UUID
    slot_date: date
    start_time: time
    end_time: time
    maximum_farmers: int
    booked_farmers: int
    is_active: bool
    created_at: datetime
