from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, constr


class NormalizedPaymentEvent(BaseModel):
    """Normalized internal representation of an external payment event."""

    event_id: str = Field(
        ...,
        description="Provider event identifier (idempotency key for event ingestion)",
    )
    external_id: str = Field(
        ...,
        description="Provider payment identifier",
    )
    merchant_id: str = Field(
        ...,
        description="Reclaim Merchant UUID. In a real system, this might be resolved from provider keys.",
    )
    amount_minor: int = Field(
        ...,
        description="Amount in integer minor units (e.g. 10000 = INR 100.00)",
    )
    currency: str = Field(..., min_length=3, max_length=3)
    status: str = Field(
        ...,
        description="Normalized status mapping to Reclaim PaymentStatus",
    )
    payment_method: str | None = None
    failure_code: str | None = None
    failure_description: str | None = None
    provider: str = Field(..., description="Provider name (e.g., demo, razorpay)")
    external_metadata: dict[str, Any] | None = None
    event_timestamp: datetime = Field(...)


class IngestionResponse(BaseModel):
    """Response returned upon successful ingestion."""

    status: str
    payment_id: str
    case_id: str | None = None
    message: str | None = None
