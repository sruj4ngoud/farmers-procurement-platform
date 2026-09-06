import uuid
from datetime import date, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Time,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin


class Slot(CreatedAtMixin, Base):
    __tablename__ = "slots"
    __table_args__ = (
        UniqueConstraint(
            "centre_id",
            "slot_date",
            "start_time",
            name="uq_slots_centre_date_start",
        ),
        CheckConstraint("maximum_farmers > 0", name="positive_maximum_farmers"),
        CheckConstraint("booked_farmers >= 0", name="non_negative_booked_farmers"),
        CheckConstraint(
            "booked_farmers <= maximum_farmers",
            name="booked_within_capacity",
        ),
        CheckConstraint("end_time > start_time", name="slot_end_after_start"),
        Index("ix_slots_centre_id_slot_date", "centre_id", "slot_date"),
    )

    slot_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    centre_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("procurement_centres.centre_id", ondelete="CASCADE"),
        nullable=False,
    )
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    maximum_farmers: Mapped[int] = mapped_column(Integer, nullable=False)
    booked_farmers: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )

    centre: Mapped["ProcurementCentre"] = relationship(back_populates="slots")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="slot")
