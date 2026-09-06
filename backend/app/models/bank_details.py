"""Bank details model with verification statuses."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

BANK_VERIFICATION_STATUSES = ("PENDING_VERIFICATION", "VERIFIED", "REJECTED")


class BankDetails(TimestampMixin, Base):
    """Farmer bank account details for receiving government procurement payments."""

    __tablename__ = "bank_details"
    __table_args__ = (
        Index("ix_bank_details_farmer_id", "farmer_id", unique=True),
    )

    bank_detail_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmers.farmer_id", ondelete="CASCADE"),
        nullable=False,
    )
    account_holder_name: Mapped[str] = mapped_column(String(120), nullable=False)
    account_number: Mapped[str] = mapped_column(String(32), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(16), nullable=False)
    # Verification status (replaces simple is_verified boolean)
    verification_status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        server_default=text("'PENDING_VERIFICATION'"),
        default="PENDING_VERIFICATION",
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Legacy boolean for backward compatibility
    @property
    def is_verified(self) -> bool:
        return self.verification_status == "VERIFIED"

    farmer: Mapped["Farmer"] = relationship(back_populates="bank_details")
    verifier: Mapped["User | None"] = relationship(foreign_keys=[verified_by])
