"""Authentication endpoints: OTP request/verify + JWT."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.auth import (
    LogoutResponse,
    OtpRequest,
    OtpRequestResponse,
    OtpVerifyRequest,
    TokenResponse,
)
from app.services.auth_service import issue_farmer_token
from app.services.otp_service import request_otp, verify_otp

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/request-otp", response_model=OtpRequestResponse)
def post_request_otp(
    payload: OtpRequest, db: Session = Depends(get_db)
) -> OtpRequestResponse:
    """Request a 6-digit OTP for a farmer's passbook + mobile number."""
    from app.config.settings import settings

    result = request_otp(db, payload.passbook_number, payload.mobile_number)
    return OtpRequestResponse(
        message="OTP sent" if not settings.otp_demo_mode else "OTP generated",
        expires_in_seconds=result["expires_in_seconds"],
        demo_otp=result["demo_otp"],
    )


@router.post("/verify-otp", response_model=TokenResponse)
def post_verify_otp(
    payload: OtpVerifyRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    """Verify an OTP and receive a JWT access token."""
    farmer = verify_otp(
        db, payload.passbook_number, payload.mobile_number, payload.otp
    )
    token, expires_in_seconds = issue_farmer_token(farmer)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        farmer_id=str(farmer.farmer_id),
        passbook_number=farmer.passbook_number,
        farmer_name=farmer.farmer_name,
        expires_in_seconds=expires_in_seconds,
    )


@router.post("/logout", response_model=LogoutResponse)
def post_logout() -> LogoutResponse:
    """Stateless logout acknowledgement.

    JWTs are stateless; clients simply discard their token. A token-revocation
    list can be added later if the security policy requires it.
    """
    return LogoutResponse(message="Successfully logged out")
