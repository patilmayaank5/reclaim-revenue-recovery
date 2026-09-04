import uuid
from enum import Enum
from pydantic import BaseModel, Field


class PolicyOutcome(str, Enum):
    """Closed set of policy evaluation outcomes."""
    ALLOW_AUTO = "allow_auto"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"


class PolicyReasonCode(str, Enum):
    """Closed set of policy decision reason codes."""
    ELIGIBLE_AUTO_EXECUTION = "eligible_auto_execution"
    HIGH_VALUE_APPROVAL_REQUIRED = "high_value_approval_required"
    MANUAL_REVIEW_ALWAYS_REQUIRES_APPROVAL = "manual_review_always_requires_approval"
    NEGATIVE_OR_ZERO_ERV = "negative_or_zero_erv"
    EXCEEDS_MAX_RECOVERY_LIMIT = "exceeds_max_recovery_limit"
    HOLDOUT_GROUP = "holdout_group"
    CASE_STOPPED = "case_stopped"
    INVALID_ASSIGNMENT = "invalid_assignment"
    FRAUD_SUSPECTED_BLOCKED = "fraud_suspected_blocked"
    MISSING_DIAGNOSIS = "missing_diagnosis"
    NO_ELIGIBLE_CANDIDATE = "no_eligible_candidate"
    NO_CANDIDATES_AVAILABLE = "no_candidates_available"
    UNSUPPORTED_INTERVENTION = "unsupported_intervention"


class PolicyLimitsConfig(BaseModel):
    """Deterministic policy limit thresholds in integer minor units."""
    auto_approval_threshold_minor: int = Field(
        default=2_000_000,
        description="Threshold above which human approval is required (e.g. â‚¹20,000.00 = 2,000,000 paise)",
    )
    max_recovery_limit_minor: int = Field(
        default=50_000_000,
        description="Hard maximum ceiling above which recovery is blocked (e.g. â‚¹500,000.00 = 50,000,000 paise)",
    )
    policy_version: str = Field(
        default="v1.0",
        description="Centralized policy version identifier for auditing",
    )


class CandidatePolicyEvaluation(BaseModel):
    """Evaluation result for an individual Phase 5 intervention candidate."""
    candidate_id: uuid.UUID
    intervention_type: str
    recoverable_amount_minor: int
    probability_bps: int
    expected_recovery_value_minor: int
    intervention_cost_minor: int
    risk_penalty_minor: int
    outcome: PolicyOutcome
    reason_code: PolicyReasonCode


class CasePolicyDecision(BaseModel):
    """Structured policy decision for a revenue-at-risk case."""
    case_id: uuid.UUID
    policy_version: str
    overall_outcome: PolicyOutcome
    selected_candidate_id: uuid.UUID | None = None
    selected_intervention_type: str | None = None
    selected_reason_code: PolicyReasonCode
    candidate_evaluations: list[CandidatePolicyEvaluation]
