"""Procurement record business logic service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProcurementRecord


def get_procurement_by_id(db: Session, procurement_id: UUID) -> ProcurementRecord | None:
    """Get procurement record by procurement_id."""
    return db.execute(
        select(ProcurementRecord).where(ProcurementRecord.procurement_id == procurement_id)
    ).scalar_one_or_none()


def get_procurement_by_booking_id(db: Session, booking_id: UUID) -> ProcurementRecord | None:
    """Get procurement record by booking_id."""
    return db.execute(
        select(ProcurementRecord).where(ProcurementRecord.booking_id == booking_id)
    ).scalar_one_or_none()
