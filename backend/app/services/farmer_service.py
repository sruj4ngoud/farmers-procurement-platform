"""Farmer business logic service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Farmer, LandRecord


def get_farmer_by_passbook_number(db: Session, passbook_number: str) -> Farmer | None:
    """Get farmer by passbook number."""
    return db.execute(
        select(Farmer).where(Farmer.passbook_number == passbook_number)
    ).scalar_one_or_none()


def get_farmer_by_id(db: Session, farmer_id) -> Farmer | None:
    """Get farmer by farmer_id."""
    return db.execute(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    ).scalar_one_or_none()


def get_lands_by_farmer(
    db: Session, farmer_id: UUID, limit: int = 50, offset: int = 0
) -> list[LandRecord]:
    """Get land records for a farmer."""
    return db.execute(
        select(LandRecord)
        .where(LandRecord.farmer_id == farmer_id)
        .order_by(LandRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()


def count_lands_by_farmer(db: Session, farmer_id: UUID) -> int:
    """Count land records for a farmer."""
    return (
        db.execute(select(LandRecord).where(LandRecord.farmer_id == farmer_id))
        .scalars()
        .all().__len__()
    )
