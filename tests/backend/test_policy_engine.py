import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.policy.rules import evaluate_candidate_policy
from app.domain.policy.schemas import (
    CandidatePolicyEvaluation,
    CasePolicyDecision,
    PolicyLimitsConfig,
    PolicyOutcome,
    PolicyReasonCode,
)
from app.models.ai_diagnosis import AIDiagnosis
from app.models.case import Case
from app.models.enums import AssignmentGroup, CaseStatus, AuditEventType
from app.models.intervention import Intervention
from app.services.policy_engine import evaluate_policy_for_case, PolicyEngineError


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def config():
    return PolicyLimitsConfig(
        auto_approval_threshold_minor=2_000_000,  # â‚¹20,000.00
        max_recovery_limit_minor=50_000_000,     # â‚¹500,000.00
        policy_version="v1.0",
    )


@pytest.fixture
def base_case():
    return Case(
        id=uuid.uuid4(),
        status=CaseStatus.DETECTED,
        assignment_group=AssignmentGroup.TREATMENT,
        amount_at_risk_minor=499_900,  # â‚¹4,999.00 (Low-value)
        currency="INR",
    )


@pytest.fixture
def base_diagnosis(base_case):
    return AIDiagnosis(
        id=uuid.uuid4(),
        case_id=base_case.id,
        diagnosis_category="insufficient_funds",
        ai_confidence=0.9,
        recovery_probability=0.7,
        model_provider="anthropic",
        model_name="claude-3-5-sonnet",
    )


@pytest.fixture
def candidate_smart_retry(base_case, base_diagnosis):
    return Intervention(
        id=uuid.uuid4(),
        case_id=base_case.id,
        diagnosis_id=base_diagnosis.id,
        intervention_type="smart_retry",
        recoverable_amount_minor=499_900,
        currency="INR",
        estimated_recovery_probability_bps=6500,
        intervention_cost_minor=5,
        risk_penalty_minor=10,
        expected_recovery_value_minor=324915,  # positive ERV
        rank=1,
    )


@pytest.fixture
def candidate_payment_link(base_case, base_diagnosis):
    return Intervention(
        id=uuid.uuid4(),
        case_id=base_case.id,
        diagnosis_id=base_diagnosis.id,
        intervention_type="payment_link",
        recoverable_amount_minor=499_900,
        currency="INR",
        estimated_recovery_probability_bps=4500,
        intervention_cost_minor=10,
        risk_penalty_minor=0,
        expected_recovery_value_minor=224945,  # positive ERV
        rank=2,
    )


@pytest.fixture
def candidate_manual_review(base_case, base_diagnosis):
    return Intervention(
        id=uuid.uuid4(),
        case_id=base_case.id,
        diagnosis_id=base_diagnosis.id,
        intervention_type="manual_review",
        recoverable_amount_minor=499_900,
        currency="INR",
        estimated_recovery_probability_bps=5000,
        intervention_cost_minor=500,
        risk_penalty_minor=0,
        expected_recovery_value_minor=249450,  # positive ERV
        rank=3,
    )


# ============================================================
# UNIT TESTS: RULE PRECEDENCE & INDIVIDUAL EVALUATION
# ============================================================

def test_rule_holdout_blocks(base_case, base_diagnosis, candidate_smart_retry, config):
    base_case.assignment_group = AssignmentGroup.HOLDOUT
    ev = evaluate_candidate_policy(candidate_smart_retry, base_case, base_diagnosis, config)
    assert ev.outcome == PolicyOutcome.BLOCK
    assert ev.reason_code == PolicyReasonCode.HOLDOUT_GROUP


def test_rule_stopped_blocks(base_case, base_diagnosis, candidate_smart_retry, config):
    base_case.status = CaseStatus.STOPPED
    ev = evaluate_candidate_policy(candidate_smart_retry, base_case, base_diagnosis, config)
    assert ev.outcome == PolicyOutcome.BLOCK
    assert ev.reason_code == PolicyReasonCode.CASE_STOPPED


def test_rule_missing_diagnosis_blocks(base_case, candidate_smart_retry, config):
    ev = evaluate_candidate_policy(candidate_smart_retry, base_case, None, config)
    assert ev.outcome == PolicyOutcome.BLOCK
    assert ev.reason_code == PolicyReasonCode.MISSING_DIAGNOSIS


def test_rule_negative_erv_blocks(base_case, base_diagnosis, candidate_smart_retry, config):
    candidate_smart_retry.expected_recovery_value_minor = -50
    ev = evaluate_candidate_policy(candidate_smart_retry, base_case, base_diagnosis, config)
    assert ev.outcome == PolicyOutcome.BLOCK
    assert ev.reason_code == PolicyReasonCode.NEGATIVE_OR_ZERO_ERV


def test_rule_fraud_blocks_automated_candidates(base_case, base_diagnosis, candidate_smart_retry, candidate_manual_review, config):
    base_diagnosis.diagnosis_category = "fraud_suspected"

    # Automated candidate is blocked
    ev_auto = evaluate_candidate_policy(candidate_smart_retry, base_case, base_diagnosis, config)
    assert ev_auto.outcome == PolicyOutcome.BLOCK
    assert ev_auto.reason_code == PolicyReasonCode.FRAUD_SUSPECTED_BLOCKED

    # Manual review candidate is NOT blocked by fraud rule, but moves to REQUIRE_APPROVAL
    ev_manual = evaluate_candidate_policy(candidate_manual_review, base_case, base_diagnosis, config)
    assert ev_manual.outcome == PolicyOutcome.REQUIRE_APPROVAL
    assert ev_manual.reason_code == PolicyReasonCode.MANUAL_REVIEW_ALWAYS_REQUIRES_APPROVAL


def test_rule_max_ceiling_overrides_approval_and_manual_review(base_case, base_diagnosis, candidate_smart_retry, candidate_manual_review, config):
    # Recoverable amount exceeds max ceiling â‚¹500,000.00 (50,000,000 minor units)
    candidate_smart_retry.recoverable_amount_minor = 60_000_000
    candidate_manual_review.recoverable_amount_minor = 60_000_000

    # Max ceiling overrides approval threshold -> BLOCK, not REQUIRE_APPROVAL
    ev_auto = evaluate_candidate_policy(candidate_smart_retry, base_case, base_diagnosis, config)
    assert ev_auto.outcome == PolicyOutcome.BLOCK
    assert ev_auto.reason_code == PolicyReasonCode.EXCEEDS_MAX_RECOVERY_LIMIT

    # Max ceiling overrides manual review -> BLOCK, not REQUIRE_APPROVAL
    ev_manual = evaluate_candidate_policy(candidate_manual_review, base_case, base_diagnosis, config)
    assert ev_manual.outcome == PolicyOutcome.BLOCK
    assert ev_manual.reason_code == PolicyReasonCode.EXCEEDS_MAX_RECOVERY_LIMIT


def test_rule_high_value_requires_approval(base_case, base_diagnosis, candidate_smart_retry, config):
    # Amount â‚¹75,000.00 (7,500,000 minor units) is between 2M and 50M threshold
    candidate_smart_retry.recoverable_amount_minor = 7_500_000
    ev = evaluate_candidate_policy(candidate_smart_retry, base_case, base_diagnosis, config)
    assert ev.outcome == PolicyOutcome.REQUIRE_APPROVAL
    assert ev.reason_code == PolicyReasonCode.HIGH_VALUE_APPROVAL_REQUIRED


def test_rule_low_value_allow_auto(base_case, base_diagnosis, candidate_smart_retry, config):
    # Amount â‚¹4,999.00 is <= 2M threshold
    ev = evaluate_candidate_policy(candidate_smart_retry, base_case, base_diagnosis, config)
    assert ev.outcome == PolicyOutcome.ALLOW_AUTO
    assert ev.reason_code == PolicyReasonCode.ELIGIBLE_AUTO_EXECUTION


def test_rule_unsupported_intervention_blocks(base_case, base_diagnosis, candidate_smart_retry, config):
    candidate_smart_retry.intervention_type = "invalid_custom_action"
    ev = evaluate_candidate_policy(candidate_smart_retry, base_case, base_diagnosis, config)
    assert ev.outcome == PolicyOutcome.BLOCK
    assert ev.reason_code == PolicyReasonCode.UNSUPPORTED_INTERVENTION


# ============================================================
# SERVICE LEVEL & SELECTION TESTS
# ============================================================

def setup_mock_session(case, diagnosis, candidates):
    session = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from cases" in stmt_str:
            result.scalar_one_or_none.return_value = case
        elif "from ai_diagnoses" in stmt_str:
            result.scalar_one_or_none.return_value = diagnosis
        elif "from interventions" in stmt_str:
            result.scalars.return_value.all.return_value = candidates
        return result

    session.execute.side_effect = mock_execute
    return session


@pytest.mark.asyncio
async def test_selection_rank1_blocked_selects_rank2(base_case, base_diagnosis, candidate_smart_retry, candidate_payment_link, config):
    # Make Rank 1 (smart_retry) BLOCKED due to negative ERV
    candidate_smart_retry.expected_recovery_value_minor = -10

    # Rank 2 (payment_link) has positive ERV
    candidates = [candidate_smart_retry, candidate_payment_link]
    session = setup_mock_session(base_case, base_diagnosis, candidates)

    decision = await evaluate_policy_for_case(session, base_case.id, config)

    # Output evaluates ALL candidates
    assert len(decision.candidate_evaluations) == 2
    assert decision.candidate_evaluations[0].outcome == PolicyOutcome.BLOCK
    assert decision.candidate_evaluations[1].outcome == PolicyOutcome.ALLOW_AUTO

    # Winning candidate is Rank 2 (payment_link)
    assert decision.overall_outcome == PolicyOutcome.ALLOW_AUTO
    assert decision.selected_candidate_id == candidate_payment_link.id
    assert decision.selected_intervention_type == "payment_link"
    assert decision.selected_reason_code == PolicyReasonCode.ELIGIBLE_AUTO_EXECUTION

    # Verify AuditEvent was logged
    assert session.add.call_count == 1
    audit_event = session.add.call_args[0][0]
    assert audit_event.event_type == AuditEventType.POLICY_EVALUATED
    assert audit_event.event_data["policy_version"] == "v1.0"
    assert audit_event.event_data["selected_candidate_id"] == str(candidate_payment_link.id)


@pytest.mark.asyncio
async def test_selection_all_blocked(base_case, base_diagnosis, candidate_smart_retry, candidate_payment_link, config):
    # Make all candidates negative ERV
    candidate_smart_retry.expected_recovery_value_minor = -10
    candidate_payment_link.expected_recovery_value_minor = -20

    candidates = [candidate_smart_retry, candidate_payment_link]
    session = setup_mock_session(base_case, base_diagnosis, candidates)

    decision = await evaluate_policy_for_case(session, base_case.id, config)

    assert decision.overall_outcome == PolicyOutcome.BLOCK
    assert decision.selected_candidate_id is None
    assert decision.selected_intervention_type is None
    assert decision.selected_reason_code == PolicyReasonCode.NO_ELIGIBLE_CANDIDATE


@pytest.mark.asyncio
async def test_selection_no_candidates(base_case, base_diagnosis, config):
    session = setup_mock_session(base_case, base_diagnosis, [])
    decision = await evaluate_policy_for_case(session, base_case.id, config)

    assert decision.overall_outcome == PolicyOutcome.BLOCK
    assert decision.selected_candidate_id is None
    assert decision.selected_reason_code == PolicyReasonCode.NO_CANDIDATES_AVAILABLE


@pytest.mark.asyncio
async def test_policy_engine_missing_case_raises_error(config):
    session = setup_mock_session(None, None, [])
    with pytest.raises(PolicyEngineError, match="not found"):
        await evaluate_policy_for_case(session, uuid.uuid4(), config)


@pytest.mark.asyncio
async def test_determinism_repeated_calls(base_case, base_diagnosis, candidate_smart_retry, candidate_payment_link, config):
    candidates = [candidate_smart_retry, candidate_payment_link]

    session1 = setup_mock_session(base_case, base_diagnosis, candidates)
    decision1 = await evaluate_policy_for_case(session1, base_case.id, config)

    session2 = setup_mock_session(base_case, base_diagnosis, candidates)
    decision2 = await evaluate_policy_for_case(session2, base_case.id, config)

    assert decision1.model_dump() == decision2.model_dump()


# ============================================================
# DEMO SCENARIOS A-F
# ============================================================

@pytest.mark.asyncio
async def test_demo_scenario_a_low_value_auto(base_case, base_diagnosis, candidate_smart_retry, config):
    # â‚¹4,999.00 failure, positive ERV -> ALLOW_AUTO
    session = setup_mock_session(base_case, base_diagnosis, [candidate_smart_retry])
    decision = await evaluate_policy_for_case(session, base_case.id, config)
    assert decision.overall_outcome == PolicyOutcome.ALLOW_AUTO
    assert decision.selected_reason_code == PolicyReasonCode.ELIGIBLE_AUTO_EXECUTION


@pytest.mark.asyncio
async def test_demo_scenario_b_high_value_approval(base_case, base_diagnosis, candidate_smart_retry, config):
    # â‚¹75,000.00 failure, positive ERV -> REQUIRE_APPROVAL
    candidate_smart_retry.recoverable_amount_minor = 7_500_000
    session = setup_mock_session(base_case, base_diagnosis, [candidate_smart_retry])
    decision = await evaluate_policy_for_case(session, base_case.id, config)
    assert decision.overall_outcome == PolicyOutcome.REQUIRE_APPROVAL
    assert decision.selected_reason_code == PolicyReasonCode.HIGH_VALUE_APPROVAL_REQUIRED


@pytest.mark.asyncio
async def test_demo_scenario_c_excessive_value_blocked(base_case, base_diagnosis, candidate_smart_retry, config):
    # â‚¹600,000.00 failure, above max ceiling -> BLOCK
    candidate_smart_retry.recoverable_amount_minor = 60_000_000
    session = setup_mock_session(base_case, base_diagnosis, [candidate_smart_retry])
    decision = await evaluate_policy_for_case(session, base_case.id, config)
    assert decision.overall_outcome == PolicyOutcome.BLOCK
    assert decision.selected_reason_code == PolicyReasonCode.NO_ELIGIBLE_CANDIDATE
    assert decision.candidate_evaluations[0].reason_code == PolicyReasonCode.EXCEEDS_MAX_RECOVERY_LIMIT


@pytest.mark.asyncio
async def test_demo_scenario_d_unrecoverable_blocked(base_case, base_diagnosis, candidate_smart_retry, config):
    # ERV <= 0 -> BLOCK
    candidate_smart_retry.expected_recovery_value_minor = 0
    session = setup_mock_session(base_case, base_diagnosis, [candidate_smart_retry])
    decision = await evaluate_policy_for_case(session, base_case.id, config)
    assert decision.overall_outcome == PolicyOutcome.BLOCK
    assert decision.selected_reason_code == PolicyReasonCode.NO_ELIGIBLE_CANDIDATE
    assert decision.candidate_evaluations[0].reason_code == PolicyReasonCode.NEGATIVE_OR_ZERO_ERV


@pytest.mark.asyncio
async def test_demo_scenario_e_holdout_blocked(base_case, base_diagnosis, candidate_smart_retry, config):
    # HOLDOUT group -> BLOCK
    base_case.assignment_group = AssignmentGroup.HOLDOUT
    session = setup_mock_session(base_case, base_diagnosis, [candidate_smart_retry])
    decision = await evaluate_policy_for_case(session, base_case.id, config)
    assert decision.overall_outcome == PolicyOutcome.BLOCK
    assert decision.selected_reason_code == PolicyReasonCode.NO_ELIGIBLE_CANDIDATE
    assert decision.candidate_evaluations[0].reason_code == PolicyReasonCode.HOLDOUT_GROUP


@pytest.mark.asyncio
async def test_demo_scenario_f_fraud_manual_review(base_case, base_diagnosis, candidate_smart_retry, candidate_manual_review, config):
    # Fraud diagnosis -> automated candidate BLOCK, manual_review REQUIRE_APPROVAL
    base_diagnosis.diagnosis_category = "fraud_suspected"
    session = setup_mock_session(base_case, base_diagnosis, [candidate_smart_retry, candidate_manual_review])
    decision = await evaluate_policy_for_case(session, base_case.id, config)

    assert decision.overall_outcome == PolicyOutcome.REQUIRE_APPROVAL
    assert decision.selected_candidate_id == candidate_manual_review.id
    assert decision.selected_reason_code == PolicyReasonCode.MANUAL_REVIEW_ALWAYS_REQUIRES_APPROVAL
    assert decision.candidate_evaluations[0].reason_code == PolicyReasonCode.FRAUD_SUSPECTED_BLOCKED
    assert decision.candidate_evaluations[1].reason_code == PolicyReasonCode.MANUAL_REVIEW_ALWAYS_REQUIRES_APPROVAL
