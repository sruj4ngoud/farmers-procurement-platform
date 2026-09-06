"""Queue token response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QueueTokenResponse(BaseModel):
    """Queue token detail response."""

    model_config = ConfigDict(from_attributes=True)

    queue_id: UUID
    booking_id: UUID
    token_number: int
    queue_status: str
    called_at: datetime | None = None
    processing_started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    # Dynamically computed 1-based position in the slot queue. None when the
    # token has left the active queue (completed/cancelled/skipped).
    position: int | None = None
