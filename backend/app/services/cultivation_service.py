"""Cultivation record business logic service."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import CONFIRMED_BOOKING_STATUSES
from app.core.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
)
from app.models import Booking, CultivationRecord, Farmer


def _as_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def get_total_cultivated_area(db: Session, farmer_id: UUID) -> Decimal:
    """Sum of all cultivated areas for a farmer."""
    total = db.execute(
        select(func.coalesce(func.sum(CultivationRecord.cultivated_area_acres), 0)).where(
            CultivationRecord.farmer_id == farmer_id
        )
    ).scalar_one()
    return Decimal(str(total))


def create_cultivation(
    db: Session,
    farmer_id: UUID,
    crop: str,
    season: str,
    cultivated_area_acres: Decimal,
    quantity_produced_quintals: Decimal,
) -> CultivationRecord:
    """Create a new cultivation record for a farmer.

    Rules enforced:
      * farmer exists
      * cultivated_area must be > 0
      * total cultivated area must not exceed registered land
      * quantity_produced must be > 0
    """
    farmer = db.execute(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    ).scalar_one_or_none()
    if farmer is None:
        raise NotFoundError("Farmer not found")

    total_land = Decimal(str(farmer.total_land_acres))

    if cultivated_area_acres > total_land:
        raise BadRequestError(
            f"Cultivated area ({cultivated_area_acres} acres) cannot exceed "
            f"your registered total land of {total_land} acres."
        )

    cultivation = CultivationRecord(
        farmer_id=farmer_id,
        crop=crop,
        season=season,
        cultivated_area_acres=cultivated_area_acres,
        quantity_produced_quintals=quantity_produced_quintals,
        quantity_to_sell_quintals=Decimal("0"),
    )
    db.add(cultivation)
    db.commit()
    db.refresh(cultivation)
    return cultivation


def get_cultivation_by_id(
    db: Session, cultivation_id: UUID
) -> CultivationRecord | None:
    """Get a cultivation record by id."""
    return db.execute(
        select(CultivationRecord).where(
            CultivationRecord.cultivation_id == cultivation_id
        )
    ).scalar_one_or_none()


def get_cultivations_by_farmer(
    db: Session, farmer_id: UUID, limit: int = 10, offset: int = 0
) -> list[CultivationRecord]:
    """Get cultivation records for a farmer with pagination."""
    return db.execute(
        select(CultivationRecord)
        .where(CultivationRecord.farmer_id == farmer_id)
        .order_by(CultivationRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()


def count_cultivations_by_farmer(db: Session, farmer_id: UUID) -> int:
    """Count total cultivation records for a farmer."""
    return (
        db.execute(
            select(CultivationRecord).where(CultivationRecord.farmer_id == farmer_id)
        ).scalars().all().__len__()
    )


def get_confirmed_booked_quantity(
    db: Session, cultivation_id: UUID
) -> Decimal:
    """Total quantity already committed via active bookings for a cultivation."""
    total = db.execute(
        select(func.coalesce(func.sum(Booking.quantity_to_sell_quintals), 0)).where(
            Booking.cultivation_id == cultivation_id,
            Booking.booking_status.in_(CONFIRMED_BOOKING_STATUSES),
        )
    ).scalar_one()
    return _as_decimal(total)


def update_quantity_to_sell(
    db: Session,
    cultivation_id: UUID,
    farmer_id: UUID,
    quantity_to_sell_quintals: Decimal,
) -> CultivationRecord:
    """Set how much of a produced crop the farmer wants to sell.

    Rules enforced:
      * farmer owns the cultivation (403 otherwise)
      * quantity_to_sell must not exceed what was actually produced
      * quantity_to_sell must not fall below what is already CONFIRMED/booked
    """
    cultivation = get_cultivation_by_id(db, cultivation_id)
    if cultivation is None:
        raise NotFoundError("Cultivation not found")
    if cultivation.farmer_id != farmer_id:
        raise ForbiddenError("Cultivation does not belong to this farmer")

    requested = _as_decimal(quantity_to_sell_quintals)
    produced = _as_decimal(cultivation.quantity_produced_quintals)

    if requested <= 0:
        raise BadRequestError("Quantity to sell must be greater than zero")

    if requested > produced:
        raise BadRequestError(
            "Quantity to sell cannot exceed the quantity produced "
            f"({produced} quintals)"
        )

    confirmed = get_confirmed_booked_quantity(db, cultivation_id)
    if requested < confirmed:
        raise BadRequestError(
            "Quantity to sell cannot be reduced below the quantity already "
            f"confirmed in bookings ({confirmed} quintals)"
        )

    cultivation.quantity_to_sell_quintals = requested
    db.commit()
    db.refresh(cultivation)
    return cultivation
