"""Notification business logic service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import (
    NOTIFICATION_BOOKING_CREATED,
    NOTIFICATION_PAYMENT_PROCESSED,
    NOTIFICATION_PROCUREMENT_COMPLETED,
    NOTIFICATION_TOKEN_GENERATED,
)
from app.models import Booking, Notification


def get_notification_by_id(db: Session, notification_id: UUID) -> Notification | None:
    """Get notification by notification_id."""
    return db.execute(
        select(Notification).where(Notification.notification_id == notification_id)
    ).scalar_one_or_none()


def get_notifications_by_farmer(
    db: Session, farmer_id: UUID, limit: int = 10, offset: int = 0
) -> list[Notification]:
    """Get notifications for a farmer with pagination (newest first)."""
    return db.execute(
        select(Notification)
        .where(Notification.farmer_id == farmer_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()


def get_unread_notifications(
    db: Session, farmer_id: UUID, limit: int = 50
) -> list[Notification]:
    """Get unread notifications for a farmer (newest first)."""
    return db.execute(
        select(Notification)
        .where(Notification.farmer_id == farmer_id, Notification.is_read.is_(False))
        .order_by(Notification.created_at.desc())
        .limit(limit)
    ).scalars().all()


def count_unread_notifications(db: Session, farmer_id: UUID) -> int:
    """Count unread notifications for a farmer."""
    return (
        db.execute(
            select(Notification).where(
                Notification.farmer_id == farmer_id,
                Notification.is_read.is_(False),
            )
        ).scalars().all().__len__()
    )


def count_notifications_by_farmer(db: Session, farmer_id: UUID) -> int:
    """Count notifications for a farmer."""
    return (
        db.execute(
            select(Notification).where(Notification.farmer_id == farmer_id)
        ).scalars().all().__len__()
    )


def create_notification(
    db: Session,
    farmer_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    booking_id: UUID | None = None,
    commit: bool = False,
) -> Notification:
    """Create an in-app notification for a farmer.

    The notification is added to the session. Pass commit=True when this call is
    not already part of a larger transaction that will be committed by the caller.
    """
    notification = Notification(
        farmer_id=farmer_id,
        booking_id=booking_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False,
    )
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    return notification


def notify_booking_created(
    db: Session, booking: Booking, commit: bool = False
) -> Notification:
    """Create the notification raised when a booking is confirmed."""
    return create_notification(
        db,
        farmer_id=booking.farmer_id,
        booking_id=booking.booking_id,
        notification_type=NOTIFICATION_BOOKING_CREATED,
        title="Booking confirmed",
        message=(
            f"Booking {booking.booking_number} for "
            f"{booking.quantity_to_sell_quintals} quintals has been confirmed."
        ),
        commit=commit,
    )


def notify_token_generated(
    db: Session, booking: Booking, token_number: int, commit: bool = False
) -> Notification:
    """Create the notification raised when a queue token is generated."""
    return create_notification(
        db,
        farmer_id=booking.farmer_id,
        booking_id=booking.booking_id,
        notification_type=NOTIFICATION_TOKEN_GENERATED,
        title="Queue token generated",
        message=(
            f"Your queue token {token_number} has been generated. "
            f"Keep this booking number handy: {booking.booking_number}."
        ),
        commit=commit,
    )


def notify_procurement_completed(
    db: Session,
    farmer_id: UUID,
    booking_id: UUID,
    accepted_quintals,
    price_per_quintal,
    commit: bool = False,
) -> Notification:
    """Create the notification raised when procurement is completed."""
    return create_notification(
        db,
        farmer_id=farmer_id,
        booking_id=booking_id,
        notification_type=NOTIFICATION_PROCUREMENT_COMPLETED,
        title="Procurement completed",
        message=(
            f"Your produce was procured successfully: {accepted_quintals} quintals "
            f"accepted at {price_per_quintal} per quintal."
        ),
        commit=commit,
    )


def notify_payment_processed(
    db: Session,
    farmer_id: UUID,
    booking_id: UUID,
    amount,
    transaction_reference: str | None = None,
    commit: bool = False,
) -> Notification:
    """Create the notification raised when a government payment is processed."""
    reference = f" (Ref: {transaction_reference})" if transaction_reference else ""
    return create_notification(
        db,
        farmer_id=farmer_id,
        booking_id=booking_id,
        notification_type=NOTIFICATION_PAYMENT_PROCESSED,
        title="Payment processed",
        message=(
            f"A government payment of {amount} has been credited to your account"
            f"{reference}."
        ),
        commit=commit,
    )


def mark_notification_read(db: Session, notification_id: UUID) -> Notification | None:
    """Mark notification as read."""
    notification = get_notification_by_id(db, notification_id)
    if notification:
        notification.is_read = True
        db.commit()
    return notification
