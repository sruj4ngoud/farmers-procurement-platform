"""Payment business logic service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment


def get_payment_by_id(db: Session, payment_id: UUID) -> Payment | None:
    """Get payment by payment_id."""
    return db.execute(
        select(Payment).where(Payment.payment_id == payment_id)
    ).scalar_one_or_none()


def get_payment_by_procurement_id(db: Session, procurement_id: UUID) -> Payment | None:
    """Get payment by procurement_id."""
    return db.execute(
        select(Payment).where(Payment.procurement_id == procurement_id)
    ).scalar_one_or_none()
