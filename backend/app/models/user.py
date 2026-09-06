import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CreatedAtMixin

USER_ROLES = ("FARMER", "CENTRE_STAFF", "DISTRICT_ADMIN")


class User(CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('FARMER', 'CENTRE_STAFF', 'DISTRICT_ADMIN')",
            name="valid_user_role",
        ),
        Index("ix_users_farmer_id", "farmer_id"),
        Index("ix_users_centre_id", "centre_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    farmer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("farmers.farmer_id", ondelete="SET NULL"),
        nullable=True,
    )
    centre_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("procurement_centres.centre_id", ondelete="SET NULL"),
        nullable=True,
    )
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), default=True
    )

    farmer: Mapped["Farmer | None"] = relationship(back_populates="users")
    centre: Mapped["ProcurementCentre | None"] = relationship(back_populates="users")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    verified_procurements: Mapped[list["ProcurementRecord"]] = relationship(
        back_populates="verifier"
    )
