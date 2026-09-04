import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VerificationStatus


class VerificationRequestPayload(BaseModel):
    """Payload for triggering verification."""
    provider: str | None = Field(None, description="Optional provider override ('simulator' or 'razorpay')")
    verification_scenario: str | None = Field(
        None,
        description="Optional scenario override for testing/demo ('recovered', 'not_recovered', 'pending', 'verification_failed')"
    )


class VerificationDetailResponse(BaseModel):
    """Schema for verification detail response."""
    id: uuid.UUID
    action_id: uuid.UUID
    case_id: uuid.UUID
    payment_id: uuid.UUID
    status: VerificationStatus
    observed_payment_status: str | None = None
    recovered_amount_minor: int | None = None
    currency: str | None = None
    provider_event_id: str | None = None
    provider_event_data: dict | None = None
    verified_at: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
