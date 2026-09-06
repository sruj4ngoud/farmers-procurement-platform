"""Payment response schemas.

Payments on this platform always flow from the Government to the farmer.
Farmers never pay money.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import PAYMENT_DIRECTION_GOVERNMENT_TO_FARMER


class PaymentResponse(BaseModel):
    """Payment detail response representing a government payment to a farmer."""

    model_config = ConfigDict(from_attributes=True)

    payment_id: UUID
    procurement_id: UUID
    amount_payable: Decimal
    payment_status: str
    transaction_reference: str | None = None
    payment_date: datetime | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    # Explicit representation of the money direction: Government -> Farmer.
    direction: str = PAYMENT_DIRECTION_GOVERNMENT_TO_FARMER
