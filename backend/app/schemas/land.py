"""Land record response schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LandRecordResponse(BaseModel):
    """Land record detail response."""

    model_config = ConfigDict(from_attributes=True)

    land_id: UUID
    farmer_id: UUID
    survey_number: str
    land_area_acres: Decimal
    land_type: str
    ownership_status: str
    created_at: datetime
