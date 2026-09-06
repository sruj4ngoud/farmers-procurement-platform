import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin


class LandRecord(CreatedAtMixin, Base):
    __tablename__ = "land_records"
    __table_args__ = (
        CheckConstraint("land_area_acres > 0", name="positive_land_area"),
        Index("ix_land_records_farmer_id", "farmer_id"),
    )

    land_id: Mapped[uuid.UUID] = mapped_column(
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
    survey_number: Mapped[str] = mapped_column(String(64), nullable=False)
    land_area_acres: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    land_type: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default=text("'AGRICULTURAL'"), default="AGRICULTURAL"
    )
    ownership_status: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default=text("'OWNED'"), default="OWNED"
    )

    farmer: Mapped["Farmer"] = relationship(back_populates="land_records")
