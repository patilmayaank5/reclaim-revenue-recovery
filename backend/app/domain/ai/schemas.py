from enum import Enum
from pydantic import BaseModel, Field

class DiagnosisCategory(str, Enum):
    """Closed-set diagnosis category compatible with Phase 2 taxonomy."""
    INSUFFICIENT_FUNDS = "insufficient_funds"
    EXPIRED_CARD = "expired_card"
    INVALID_DETAILS = "invalid_details"
    FRAUD_SUSPECTED = "fraud_suspected"
    TECHNICAL_FAILURE = "technical_failure"
    UNKNOWN = "unknown"

class AIDiagnosisOutput(BaseModel):
    """Structured output expected from the AI provider.

    IMPORTANT:
    - ai_confidence: Raw AI model confidence in this diagnosis (0.0 - 1.0).
    - recovery_probability: ADVISORY AI estimate of recovery success (0.0 - 1.0).
      This is NOT authoritative for ERV/policy calculation.
    """
    diagnosis_category: DiagnosisCategory = Field(
        ...,
        description="The primary diagnosed failure reason category."
    )
    reason: str = Field(
        ...,
        description="Detailed text explanation of the diagnosis."
    )
    ai_confidence: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Confidence level in the diagnosis."
    )
    recovery_probability: float | None = Field(
        None,
        ge=0.0, le=1.0,
        description="Advisory AI estimate of recovery probability. NOT authoritative."
    )
    evidence: dict = Field(
        ...,
        description="Structured key-value pairs of evidence extracted from input."
    )
    uncertainty: str = Field(
        ...,
        description="Description of any uncertainty or missing information."
    )
