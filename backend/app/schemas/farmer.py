"""Farmer response schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


def mask_pan(pan: str | None) -> str | None:
    """Mask PAN number showing only last 4 characters."""
    if pan is None or len(pan) < 4:
        return pan
    return "X" * (len(pan) - 4) + pan[-4:]


def mask_mobile(mobile: str) -> str:
    """Mask mobile number showing only last 4 digits."""
    if len(mobile) < 4:
        return mobile
    return mobile[:2] + "X" * (len(mobile) - 4) + mobile[-2:]


class FarmerResponse(BaseModel):
    """Farmer detail response."""

    model_config = ConfigDict(from_attributes=True)

    farmer_id: UUID
    passbook_number: str
    farmer_name: str
    mobile_number: str
    village: str
    mandal: str
    district: str
    state: str | None = None
    survey_number: str
    total_land_acres: Decimal
    pan_number: str | None = None
    pan_number_masked: str | None = None
    mobile_number_masked: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    created_at: datetime
    updated_at: datetime
