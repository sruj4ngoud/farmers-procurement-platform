"""Payment model with government-to-farmer payment statuses."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

PAYMENT_STATUSES = ("PENDING", "READY", "PROCESSING", "COMPLETED", "FAILED")


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_payable >= 0", name="non_negative_amount"),
        CheckConstraint(
            "payment_status IN ('PENDING', 'READY', 'PROCESSING', 'COMPLETED', 'FAILED')",
            name="valid_payment_status",
        ),
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    procurement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("procurement_records.procurement_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    amount_payable: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'PENDING'"),
        default="PENDING",
    )
    payment_direction: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'GOVERNMENT_TO_FARMER'"),
        default="GOVERNMENT_TO_FARMER",
    )
    transaction_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_credit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    procurement: Mapped["ProcurementRecord"] = relationship(back_populates="payment")
