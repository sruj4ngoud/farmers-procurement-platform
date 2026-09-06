import uuid

from sqlalchemy import Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin


class District(CreatedAtMixin, Base):
    __tablename__ = "districts"
    __table_args__ = (
        Index("ix_districts_name", "name"),
    )

    district_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)

    mandals: Mapped[list["Mandal"]] = relationship(back_populates="district")
