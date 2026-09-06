"""Issue/Exception model for tracking admin operational issues."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin

ISSUE_STATUSES = ("OPEN", "IN_PROGRESS", "RESOLVED", "IGNORED")
ISSUE_SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
ISSUE_TYPES = (
    "DUPLICATE_BOOKING",
    "QUANTITY_MISMATCH",
    "SLOT_CAPACITY_CONFLICT",
    "CENTRE_INACTIVE",
    "PAYMENT_FAILED",
    "BANK_VERIFICATION_FAILED",
    "BOOKING_PENDING_TOO_LONG",
    "UNUSUAL_QUANTITY",
    "PROCUREMENT_DELAYED",
    "OTHER",
)


class Issue(CreatedAtMixin, Base):
    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issues_status", "status"),
        Index("ix_issues_severity", "severity"),
        Index("ix_issues_issue_type", "issue_type"),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    issue_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="MEDIUM")
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'OPEN'"), default="OPEN"
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    resolution_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    resolver: Mapped["User | None"] = relationship(foreign_keys=[resolved_by])
