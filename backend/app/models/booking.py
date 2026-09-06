"""Booking model with admin review workflow."""

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

BOOKING_STATUSES = (
    "PENDING_ADMIN_REVIEW",
    "ACCEPTED",
    "REJECTED",
    "AUTO_ACCEPTED",
    "CANCELLED",
    "COMPLETED",
    "NO_SHOW",
    # Legacy status kept for backward compatibility
    "CONFIRMED",
)


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("quantity_to_sell_quintals > 0", name="positive_booking_qty"),
        CheckConstraint(
            "booking_status IN ('PENDING_ADMIN_REVIEW', 'ACCEPTED', 'REJECTED', "
            "'AUTO_ACCEPTED', 'CANCELLED', 'COMPLETED', 'NO_SHOW', 'CONFIRMED')",
            name="valid_booking_status",
        ),
        Index("ix_bookings_farmer_id", "farmer_id"),
        Index("ix_bookings_centre_id", "centre_id"),
        Index("ix_bookings_slot_id", "slot_id"),
        Index("ix_bookings_cultivation_id", "cultivation_id"),
        Index("ix_bookings_booking_status", "booking_status"),
    )

    booking_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    booking_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmers.farmer_id", ondelete="RESTRICT"),
        nullable=False,
    )
    cultivation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cultivation_records.cultivation_id", ondelete="RESTRICT"),
        nullable=False,
    )
    centre_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("procurement_centres.centre_id", ondelete="RESTRICT"),
        nullable=False,
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("slots.slot_id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_to_sell_quintals: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    booking_status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        server_default=text("'PENDING_ADMIN_REVIEW'"),
        default="PENDING_ADMIN_REVIEW",
    )

    # Admin review fields
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    farmer: Mapped["Farmer"] = relationship(back_populates="bookings")
    cultivation: Mapped["CultivationRecord"] = relationship(back_populates="bookings")
    centre: Mapped["ProcurementCentre"] = relationship(back_populates="bookings")
    slot: Mapped["Slot"] = relationship(back_populates="bookings")
    queue_token: Mapped["QueueToken | None"] = relationship(
        back_populates="booking", uselist=False
    )
    procurement_record: Mapped["ProcurementRecord | None"] = relationship(
        back_populates="booking", uselist=False
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="booking")
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])
