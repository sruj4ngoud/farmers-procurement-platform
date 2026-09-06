import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin


class CultivationRecord(CreatedAtMixin, Base):
    __tablename__ = "cultivation_records"
    __table_args__ = (
        CheckConstraint("cultivated_area_acres > 0", name="positive_cultivated_area"),
        CheckConstraint("quantity_produced_quintals > 0", name="positive_produced"),
        CheckConstraint("quantity_to_sell_quintals >= 0", name="non_negative_to_sell"),
        CheckConstraint(
            "quantity_to_sell_quintals <= quantity_produced_quintals",
            name="sell_not_exceed_produced",
        ),
        Index("ix_cultivation_records_farmer_id", "farmer_id"),
        Index("ix_cultivation_records_crop", "crop"),
    )

    cultivation_id: Mapped[uuid.UUID] = mapped_column(
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
    season: Mapped[str] = mapped_column(String(32), nullable=False)
    cultivated_area_acres: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    crop: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_produced_quintals: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_to_sell_quintals: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        server_default=text("0"),
        default=Decimal("0"),
    )

    farmer: Mapped["Farmer"] = relationship(back_populates="cultivation_records")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="cultivation")
