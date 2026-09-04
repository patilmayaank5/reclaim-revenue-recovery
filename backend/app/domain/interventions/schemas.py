from enum import Enum
from pydantic import BaseModel, Field

class InterventionType(str, Enum):
    SMART_RETRY = "smart_retry"
    PAYMENT_LINK = "payment_link"
    DUNNING_EMAIL = "dunning_email"
    MANUAL_REVIEW = "manual_review"

class ERVCalculationParams(BaseModel):
    probability_bps: int = Field(ge=0, le=10000)
    recoverable_amount_minor: int
    intervention_cost_minor: int
    risk_penalty_minor: int

class ERVCalculationResult(BaseModel):
    expected_recovery_minor: int
    erv_minor: int

class CalibrationInput(BaseModel):
    intervention_type: InterventionType
    diagnosis_category: str
    ai_recovery_probability: float | None = Field(None, ge=0.0, le=1.0)
