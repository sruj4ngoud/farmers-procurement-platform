import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, Integer, Numeric, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

CENTRE_STATUSES = ("ACTIVE", "LIMITED", "FULL", "INACTIVE")


class ProcurementCentre(TimestampMixin, Base):
    __tablename__ = "procurement_centres"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="positive_capacity"),
        CheckConstraint(
            "current_status IN ('ACTIVE', 'LIMITED', 'FULL', 'INACTIVE')",
            name="valid_centre_status",
        ),
        Index("ix_procurement_centres_latitude_longitude", "latitude", "longitude"),
        Index("ix_procurement_centres_current_status", "current_status"),
    )

    centre_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    centre_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    centre_name: Mapped[str] = mapped_column(String(160), nullable=False)
    agency: Mapped[str] = mapped_column(String(64), nullable=False)
    village: Mapped[str] = mapped_column(String(120), nullable=False)
    mandal: Mapped[str] = mapped_column(String(120), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_status: Mapped[str] = mapped_column(String(16), nullable=False)

    slots: Mapped[list["Slot"]] = relationship(back_populates="centre")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="centre")
    users: Mapped[list["User"]] = relationship(back_populates="centre")
