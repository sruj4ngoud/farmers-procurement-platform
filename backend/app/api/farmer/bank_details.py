"""Farmer bank details endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import get_current_farmer
from app.database.connection import get_db
from app.schemas.bank_details import (
    BankDetailsCreateRequest,
    BankDetailsResponse,
    BankDetailsOTPVerifyRequest,
)
from app.services.bank_details_service import (
    build_bank_details_response,
    create_or_update_bank_details,
    get_bank_details_by_farmer,
    verify_bank_details,
)
from app.services.otp_service import request_otp as send_otp, verify_otp

router = APIRouter(prefix="/api/farmer", tags=["farmer"])


@router.get("/bank-details")
def get_bank_details(
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Get the authenticated farmer's bank details (masked)."""
    bank_details = get_bank_details_by_farmer(db, farmer.farmer_id)
    if bank_details is None:
        return None
    return build_bank_details_response(bank_details)


@router.post("/bank-details", response_model=BankDetailsResponse)
def save_bank_details(
    payload: BankDetailsCreateRequest,
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Save or update bank details for the authenticated farmer."""
    bank_details = create_or_update_bank_details(
        db=db,
        farmer_id=farmer.farmer_id,
        account_holder_name=payload.account_holder_name,
        account_number=payload.account_number,
        ifsc_code=payload.ifsc_code,
    )
    return build_bank_details_response(bank_details)


@router.post("/bank-details/request-otp")
def request_bank_otp(
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Send OTP to farmer's mobile for bank details verification."""
    result = send_otp(db, farmer.passbook_number, farmer.mobile_number)
    from app.config.settings import settings
    return {
        "message": "OTP sent" if not settings.otp_demo_mode else "OTP generated",
        "expires_in_seconds": result["expires_in_seconds"],
        "demo_otp": result.get("demo_otp"),
    }


@router.post("/bank-details/verify-otp")
def verify_bank_otp(
    payload: BankDetailsOTPVerifyRequest,
    farmer=Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Verify OTP and mark bank details as verified."""
    # Verify OTP
    verify_otp(db, farmer.passbook_number, farmer.mobile_number, payload.otp)

    # Mark bank details as verified
    bank_details = verify_bank_details(db, farmer.farmer_id)
    return build_bank_details_response(bank_details)
