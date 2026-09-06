"""Notification endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.core.permissions import get_optional_current_farmer
from app.database.connection import get_db
from app.schemas.notification import NotificationResponse
from app.services.farmer_service import get_farmer_by_passbook_number
from app.services.notification_service import (
    get_notification_by_id,
    get_notifications_by_farmer,
    mark_notification_read,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/{passbook_number}", response_model=list[NotificationResponse])
async def get_farmer_notifications(
    passbook_number: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get notifications for a farmer.

    This is the public Phase 4 read endpoint keyed by passbook number.
    """
    farmer = get_farmer_by_passbook_number(db, passbook_number)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    notifications = get_notifications_by_farmer(db, farmer.farmer_id, limit, offset)
    return notifications


@router.put(
    "/{notification_id}/read", response_model=NotificationResponse
)
async def mark_as_read(
    notification_id: str,
    farmer=Depends(get_optional_current_farmer),
    db: Session = Depends(get_db),
):
    """Mark a notification as read.

    Authenticated callers may only read their own notifications (403 otherwise).
    Unauthenticated access preserves the public Phase 4 behaviour.
    """
    try:
        notification_uuid = UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification ID format")

    notification = get_notification_by_id(db, notification_uuid)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if farmer is not None and notification.farmer_id != farmer.farmer_id:
        raise ForbiddenError("Notification does not belong to this farmer")

    return mark_notification_read(db, notification_uuid)
