"""Procurement centre business logic service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProcurementCentre


def get_centre_by_id(db: Session, centre_id: UUID) -> ProcurementCentre | None:
    """Get centre by centre_id."""
    return db.execute(
        select(ProcurementCentre).where(ProcurementCentre.centre_id == centre_id)
    ).scalar_one_or_none()


def get_all_centres(
    db: Session, limit: int = 10, offset: int = 0
) -> list[ProcurementCentre]:
    """Get all centres with pagination."""
    return db.execute(
        select(ProcurementCentre).limit(limit).offset(offset)
    ).scalars().all()


def count_all_centres(db: Session) -> int:
    """Count total centres."""
    return db.execute(select(ProcurementCentre)).scalars().all().__len__()


def get_active_centres(
    db: Session, limit: int = 10, offset: int = 0
) -> list[ProcurementCentre]:
    """Get all active centres with pagination."""
    return db.execute(
        select(ProcurementCentre)
        .where(ProcurementCentre.current_status.in_(["ACTIVE", "LIMITED"]))
        .limit(limit)
        .offset(offset)
    ).scalars().all()


def get_centres_with_coordinates(db: Session) -> list[ProcurementCentre]:
    """Get all centres that have latitude/longitude."""
    return db.execute(
        select(ProcurementCentre).where(
            (ProcurementCentre.latitude.isnot(None))
            & (ProcurementCentre.longitude.isnot(None))
        )
    ).scalars().all()
