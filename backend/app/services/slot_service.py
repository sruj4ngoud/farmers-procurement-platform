"""Slot business logic service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Slot


def get_slot_by_id(db: Session, slot_id: UUID) -> Slot | None:
    """Get slot by slot_id."""
    return db.execute(
        select(Slot).where(Slot.slot_id == slot_id)
    ).scalar_one_or_none()


def get_all_slots(
    db: Session, limit: int = 10, offset: int = 0
) -> list[Slot]:
    """Get all slots with pagination."""
    return db.execute(
        select(Slot).limit(limit).offset(offset)
    ).scalars().all()


def count_all_slots(db: Session) -> int:
    """Count total slots."""
    return db.execute(select(Slot)).scalars().all().__len__()


def get_slots_by_centre(
    db: Session, centre_id: UUID, limit: int = 10, offset: int = 0
) -> list[Slot]:
    """Get slots for a centre with pagination."""
    return db.execute(
        select(Slot)
        .where(Slot.centre_id == centre_id)
        .limit(limit)
        .offset(offset)
    ).scalars().all()


def count_slots_by_centre(db: Session, centre_id: UUID) -> int:
    """Count slots for a centre."""
    return db.execute(
        select(Slot).where(Slot.centre_id == centre_id)
    ).scalars().all().__len__()
