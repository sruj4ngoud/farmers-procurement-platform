import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin

QUEUE_STATUSES = (
    "WAITING",
    "CALLED",
    "PROCESSING",
    "COMPLETED",
    "SKIPPED",
    "CANCELLED",
)


class QueueToken(CreatedAtMixin, Base):
    __tablename__ = "queue_tokens"
    __table_args__ = (
        CheckConstraint("token_number > 0", name="positive_token_number"),
        CheckConstraint(
            "queue_status IN ('WAITING', 'CALLED', 'PROCESSING', 'COMPLETED', 'SKIPPED', 'CANCELLED')",
            name="valid_queue_status",
        ),
        Index("ix_queue_tokens_queue_status", "queue_status"),
    )

    queue_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bookings.booking_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    token_number: Mapped[int] = mapped_column(Integer, nullable=False)
    queue_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'WAITING'"),
        default="WAITING",
    )
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    booking: Mapped["Booking"] = relationship(back_populates="queue_token")
