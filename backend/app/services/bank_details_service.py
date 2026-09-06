"""Bank details business logic service."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import BankDetails, Farmer


def mask_account_number(account_number: str) -> str:
    """Mask account number showing only last 4 digits."""
    if len(account_number) <= 4:
        return account_number
    return "X" * (len(account_number) - 4) + account_number[-4:]


def mask_ifsc(ifsc_code: str) -> str:
    """Mask IFSC showing only last 3 characters."""
    if len(ifsc_code) <= 3:
        return ifsc_code
    return "X" * (len(ifsc_code) - 3) + ifsc_code[-3:]


def get_bank_details_by_farmer(db: Session, farmer_id: UUID) -> BankDetails | None:
    """Get bank details for a farmer."""
    return db.execute(
        select(BankDetails).where(BankDetails.farmer_id == farmer_id)
    ).scalar_one_or_none()


def create_or_update_bank_details(
    db: Session,
    farmer_id: UUID,
    account_holder_name: str,
    account_number: str,
    ifsc_code: str,
) -> BankDetails:
    """Create or update bank details for a farmer."""
    # Validate farmer exists
    farmer = db.execute(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    ).scalar_one_or_none()
    if farmer is None:
        raise NotFoundError("Farmer not found")

    existing = get_bank_details_by_farmer(db, farmer_id)

    if existing:
        existing.account_holder_name = account_holder_name
        existing.account_number = account_number
        existing.ifsc_code = ifsc_code
        existing.is_verified = False
        existing.verified_at = None
        db.commit()
        db.refresh(existing)
        return existing
    else:
        bank_details = BankDetails(
            farmer_id=farmer_id,
            account_holder_name=account_holder_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            is_verified=False,
        )
        db.add(bank_details)
        db.commit()
        db.refresh(bank_details)
        return bank_details


def verify_bank_details(db: Session, farmer_id: UUID) -> BankDetails:
    """Mark bank details as verified after OTP verification."""
    bank_details = get_bank_details_by_farmer(db, farmer_id)
    if bank_details is None:
        raise NotFoundError("Bank details not found. Please save bank details first.")

    bank_details.is_verified = True
    bank_details.verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(bank_details)
    return bank_details


def build_bank_details_response(bank_details: BankDetails) -> dict:
    """Build masked bank details response."""
    return {
        "bank_detail_id": bank_details.bank_detail_id,
        "farmer_id": bank_details.farmer_id,
        "account_holder_name": bank_details.account_holder_name,
        "account_number_masked": mask_account_number(bank_details.account_number),
        "ifsc_code_masked": mask_ifsc(bank_details.ifsc_code),
        "is_verified": bank_details.is_verified,
        "verified_at": bank_details.verified_at,
        "created_at": bank_details.created_at,
        "updated_at": bank_details.updated_at,
    }
