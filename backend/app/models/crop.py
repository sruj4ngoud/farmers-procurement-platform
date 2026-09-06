"""Crop master data model with MSP."""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Date, Index, Numeric, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Crop(TimestampMixin, Base):
    __tablename__ = "crops"
    __table_args__ = (
        Index("ix_crops_crop_name", "crop_name"),
        Index("ix_crops_crop_category", "crop_category"),
        Index("ix_crops_is_active", "is_active"),
    )

    crop_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    crop_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    crop_category: Mapped[str] = mapped_column(String(60), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )
    # MSP stored on crop record for historical lookups
    msp_per_quintal: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    msp_effective_date: Mapped[str | None] = mapped_column(Date, nullable=True)
