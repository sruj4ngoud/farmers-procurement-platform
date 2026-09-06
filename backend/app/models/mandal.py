import uuid

from sqlalchemy import ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin


class Mandal(CreatedAtMixin, Base):
    __tablename__ = "mandals"
    __table_args__ = (
        Index("ix_mandals_district_id", "district_id"),
    )

    mandal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    district_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("districts.district_id", ondelete="CASCADE"),
        nullable=False,
    )

    district: Mapped["District"] = relationship(back_populates="mandals")
