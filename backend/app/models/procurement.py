import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin

PROCUREMENT_STATUSES = ("PENDING", "PROCESSING", "COMPLETED", "REJECTED")


class ProcurementRecord(CreatedAtMixin, Base):
    __tablename__ = "procurement_records"
    __table_args__ = (
        CheckConstraint("quantity_submitted_quintals > 0", name="positive_submitted"),
        CheckConstraint("quantity_accepted_quintals >= 0", name="non_negative_accepted"),
        CheckConstraint("price_per_quintal > 0", name="positive_price"),
        CheckConstraint(
            "quantity_accepted_quintals <= quantity_submitted_quintals",
            name="accepted_not_exceed_submitted",
        ),
        CheckConstraint(
            "procurement_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'REJECTED')",
            name="valid_procurement_status",
        ),
        Index("ix_procurement_records_verified_by", "verified_by"),
    )

    procurement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bookings.booking_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    quantity_submitted_quintals: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_accepted_quintals: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_per_quintal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    procurement_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'PENDING'"),
        default="PENDING",
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    booking: Mapped["Booking"] = relationship(back_populates="procurement_record")
    verifier: Mapped["User | None"] = relationship(back_populates="verified_procurements")
    payment: Mapped["Payment | None"] = relationship(back_populates="procurement", uselist=False)
