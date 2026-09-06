"""Procurement centre response schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CentreResponse(BaseModel):
    """Procurement centre detail response."""

    model_config = ConfigDict(from_attributes=True)

    centre_id: UUID
    centre_code: str
    centre_name: str
    agency: str
    village: str
    mandal: str
    district: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    capacity: int
    current_status: str
    created_at: datetime
    updated_at: datetime


class CentreWithDistanceResponse(CentreResponse):
    """Centre response with calculated distance in km."""

    distance_km: Decimal
