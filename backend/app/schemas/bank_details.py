"""Bank details schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BankDetailsCreateRequest(BaseModel):
    """Request body for creating/updating bank details."""

    account_holder_name: str = Field(min_length=1, max_length=120)
    account_number: str = Field(min_length=6, max_length=32)
    ifsc_code: str = Field(min_length=6, max_length=16)


class BankDetailsResponse(BaseModel):
    """Bank details response (masked account number)."""

    model_config = ConfigDict(from_attributes=True)

    bank_detail_id: UUID
    farmer_id: UUID
    account_holder_name: str
    account_number_masked: str
    ifsc_code_masked: str
    is_verified: bool
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class BankDetailsOTPRequest(BaseModel):
    """Request to send OTP for bank details verification."""

    pass


class BankDetailsOTPVerifyRequest(BaseModel):
    """Request to verify OTP for bank details."""

    otp: str = Field(min_length=6, max_length=6)
