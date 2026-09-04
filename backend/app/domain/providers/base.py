import uuid
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel, Field

from app.models.enums import VerificationStatus


class ExecutionResultStatus(str, Enum):
    """Closed set of execution result outcomes."""
    SUCCESS = "success"
    TRANSIENT_FAILURE = "transient_failure"
    PERMANENT_FAILURE = "permanent_failure"
    AMBIGUOUS_TIMEOUT = "ambiguous_timeout"


class ExecutionRequest(BaseModel):
    """Normalized execution request payload passed to provider adapters."""
    action_id: uuid.UUID
    case_id: uuid.UUID
    payment_id: uuid.UUID | None = None
    amount_minor: int = Field(..., description="Recoverable amount in minor integer units")
    currency: str = Field(..., max_length=3, description="ISO 4217 currency code")
    intervention_type: str
    idempotency_key: str
    metadata: dict = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    """Normalized allowlisted execution response from provider adapters."""
    status: ExecutionResultStatus
    provider_transaction_id: str | None = None
    error_code: str | None = None
    error_class: str | None = None
    requires_verification: bool = False
    ambiguous: bool = False
    attempt_timestamp: str = Field(..., description="ISO 8601 creation timestamp of execution response")


class ExecutionProvider(ABC):
    """Abstract Base Class for all recovery execution provider adapters."""

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Executes a recovery intervention through the provider integration."""
        pass

    @abstractmethod
    async def verify(self, request: "VerificationRequest") -> "VerificationResponse":
        """Verifies payment recovery status through provider evidence lookup."""
        pass


class VerificationRequest(BaseModel):
    """Normalized verification request payload passed to provider adapters."""
    action_id: uuid.UUID
    case_id: uuid.UUID
    payment_id: uuid.UUID
    provider: str
    provider_transaction_id: str | None = None
    intervention_type: str
    amount_minor: int = Field(..., description="Recoverable amount in minor integer units")
    currency: str = Field(..., max_length=3, description="ISO 4217 currency code")
    metadata: dict = Field(default_factory=dict)


class VerificationResponse(BaseModel):
    """Normalized allowlisted verification response from provider adapters."""
    status: VerificationStatus
    observed_payment_status: str | None = None
    recovered_amount_minor: int | None = None
    currency: str | None = None
    provider_event_id: str | None = None
    provider_event_data: dict | None = None
    verified_at: str | None = Field(None, description="ISO 8601 creation timestamp of verification response")
