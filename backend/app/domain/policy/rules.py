from app.domain.interventions.schemas import InterventionType
from app.domain.policy.schemas import (
    CandidatePolicyEvaluation,
    PolicyLimitsConfig,
    PolicyOutcome,
    PolicyReasonCode,
)
from app.models.ai_diagnosis import AIDiagnosis
from app.models.case import Case
from app.models.enums import AssignmentGroup, CaseStatus
from app.models.intervention import Intervention


def evaluate_candidate_policy(
    candidate: Intervention,
    case: Case,
    diagnosis: AIDiagnosis | None,
    config: PolicyLimitsConfig,
) -> CandidatePolicyEvaluation:
    """Evaluates a single intervention candidate against deterministic policy rules.

    Precedence order (First-Failing-Rule Wins):
    1. Case / Assignment Safety Gates
    2. Economic Viability (ERV <= 0)
    3. Fraud / Risk Restrictions
    4. Maximum Recovery Ceiling (overrides approval threshold)
    5. Intervention-Specific Restrictions (manual_review)
    6. Human Approval Threshold
    7. Auto-Execution Approval (ALLOW_AUTO)
    """

    # Helper to construct candidate evaluation
    def build_eval(outcome: PolicyOutcome, reason_code: PolicyReasonCode) -> CandidatePolicyEvaluation:
        return CandidatePolicyEvaluation(
            candidate_id=candidate.id,
            intervention_type=candidate.intervention_type,
            recoverable_amount_minor=candidate.recoverable_amount_minor,
            probability_bps=candidate.estimated_recovery_probability_bps,
            expected_recovery_value_minor=candidate.expected_recovery_value_minor,
            intervention_cost_minor=candidate.intervention_cost_minor,
            risk_penalty_minor=candidate.risk_penalty_minor,
            outcome=outcome,
            reason_code=reason_code,
        )

    # Validate valid intervention type
    try:
        InterventionType(candidate.intervention_type)
    except ValueError:
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.UNSUPPORTED_INTERVENTION)

    # 1. Case & Assignment Safety Gates
    if case.assignment_group == AssignmentGroup.HOLDOUT:
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.HOLDOUT_GROUP)

    if case.assignment_group != AssignmentGroup.TREATMENT:
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.INVALID_ASSIGNMENT)

    if case.status == CaseStatus.STOPPED:
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.CASE_STOPPED)

    if diagnosis is None:
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.MISSING_DIAGNOSIS)

    # Validate economic bounds
    if (
        candidate.estimated_recovery_probability_bps < 0
        or candidate.estimated_recovery_probability_bps > 10000
    ):
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.UNSUPPORTED_INTERVENTION)

    # 2. Economic Viability
    if candidate.expected_recovery_value_minor <= 0:
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.NEGATIVE_OR_ZERO_ERV)

    # 3. Fraud / Risk Restrictions
    if (
        diagnosis.diagnosis_category == "fraud_suspected"
        and candidate.intervention_type != InterventionType.MANUAL_REVIEW.value
    ):
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.FRAUD_SUSPECTED_BLOCKED)

    # 4. Maximum Recovery Ceiling (hard limit, overrides approval threshold & manual_review)
    if candidate.recoverable_amount_minor > config.max_recovery_limit_minor:
        return build_eval(PolicyOutcome.BLOCK, PolicyReasonCode.EXCEEDS_MAX_RECOVERY_LIMIT)

    # 5. Intervention-Specific Restrictions (manual_review always requires human approval)
    if candidate.intervention_type == InterventionType.MANUAL_REVIEW.value:
        return build_eval(
            PolicyOutcome.REQUIRE_APPROVAL,
            PolicyReasonCode.MANUAL_REVIEW_ALWAYS_REQUIRES_APPROVAL,
        )

    # 6. Human Approval Threshold
    if candidate.recoverable_amount_minor > config.auto_approval_threshold_minor:
        return build_eval(
            PolicyOutcome.REQUIRE_APPROVAL,
            PolicyReasonCode.HIGH_VALUE_APPROVAL_REQUIRED,
        )

    # 7. Auto-Execution Approval
    return build_eval(PolicyOutcome.ALLOW_AUTO, PolicyReasonCode.ELIGIBLE_AUTO_EXECUTION)
