"""Notification response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Notification detail response."""

    model_config = ConfigDict(from_attributes=True)

    notification_id: UUID
    farmer_id: UUID
    booking_id: UUID | None = None
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
