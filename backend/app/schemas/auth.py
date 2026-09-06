"""Auth (OTP + JWT) request/response schemas."""

from pydantic import BaseModel, Field

from app.core.constants import OTP_DEFAULT_LENGTH


class OtpRequest(BaseModel):
    """Request an OTP for a farmer identified by passbook + mobile."""

    passbook_number: str = Field(min_length=1, max_length=32)
    mobile_number: str = Field(min_length=6, max_length=15)


class OtpVerifyRequest(BaseModel):
    """Verify an OTP and exchange it for a JWT."""

    passbook_number: str = Field(min_length=1, max_length=32)
    mobile_number: str = Field(min_length=6, max_length=15)
    otp: str = Field(min_length=OTP_DEFAULT_LENGTH, max_length=OTP_DEFAULT_LENGTH)


class OtpRequestResponse(BaseModel):
    """Response for a successful OTP request."""

    message: str
    expires_in_seconds: int
    # Present only in demo/test mode so the farmer journey can be exercised
    # without a real SMS gateway. Never populated in production.
    demo_otp: str | None = None


class TokenResponse(BaseModel):
    """JWT issued after successful OTP verification."""

    access_token: str
    token_type: str = "bearer"
    farmer_id: str
    passbook_number: str
    farmer_name: str
    expires_in_seconds: int


class LogoutResponse(BaseModel):
    """Stateless logout acknowledgement."""

    message: str
