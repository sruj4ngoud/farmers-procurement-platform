import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, Index, Numeric, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Farmer(TimestampMixin, Base):
    __tablename__ = "farmers"
    __table_args__ = (
        CheckConstraint("total_land_acres > 0", name="positive_land"),
        Index("ix_farmers_mobile_number", "mobile_number"),
        Index("ix_farmers_latitude_longitude", "latitude", "longitude"),
    )

    farmer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    passbook_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    farmer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    mobile_number: Mapped[str] = mapped_column(String(15), nullable=False)
    village: Mapped[str] = mapped_column(String(120), nullable=False)
    mandal: Mapped[str] = mapped_column(String(120), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    survey_number: Mapped[str] = mapped_column(String(64), nullable=False)
    total_land_acres: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pan_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)

    land_records: Mapped[list["LandRecord"]] = relationship(back_populates="farmer")
    cultivation_records: Mapped[list["CultivationRecord"]] = relationship(
        back_populates="farmer"
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="farmer")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="farmer")
    users: Mapped[list["User"]] = relationship(back_populates="farmer")
    bank_details: Mapped["BankDetails | None"] = relationship(
        back_populates="farmer", uselist=False
    )
