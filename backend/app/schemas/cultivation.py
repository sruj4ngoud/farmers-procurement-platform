"""Cultivation record response schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CultivationResponse(BaseModel):
    """Cultivation record detail response."""

    model_config = ConfigDict(from_attributes=True)

    cultivation_id: UUID
    farmer_id: UUID
    season: str
    cultivated_area_acres: Decimal
    crop: str
    quantity_produced_quintals: Decimal
    quantity_to_sell_quintals: Decimal
    created_at: datetime


class CultivationCreateRequest(BaseModel):
    """Request body for creating a new cultivation record."""

    crop: str = Field(min_length=1, max_length=64)
    season: str = Field(min_length=1, max_length=32)
    cultivated_area_acres: Decimal = Field(gt=0, le=10_000)
    quantity_produced_quintals: Decimal = Field(gt=0, le=10_000_000)


class QuantityToSellUpdateRequest(BaseModel):
    """Request body for updating how much of a produced crop a farmer sells."""

    quantity_to_sell_quintals: Decimal = Field(gt=0, le=10_000_000)
