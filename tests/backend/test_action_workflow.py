import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.actions.schemas import ActionCreateResponse, ActionDetailResponse
from app.domain.policy.schemas import CasePolicyDecision, PolicyOutcome, PolicyReasonCode
from app.models.action import Action
from app.models.ai_diagnosis import AIDiagnosis
from app.models.approval import Approval
from app.models.case import Case
from app.models.enums import ActionStatus, ApprovalStatus, AssignmentGroup, AuditEventType, CaseStatus
from app.models.intervention import Intervention
from app.services.action_service import (
    ActionWorkflowError,
    InvalidApprovalStateError,
    StalePolicyAuthorizationError,
    create_action_for_case,
    decide_approval,
    get_action_details,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def base_case():
    return Case(
        id=uuid.uuid4(),
        status=CaseStatus.DETECTED,
        assignment_group=AssignmentGroup.TREATMENT,
        amount_at_risk_minor=499_900,
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
def base_candidate(base_case, base_diagnosis):
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
        expected_recovery_value_minor=324915,
        rank=1,
    )


def setup_mock_session(case, diagnosis, candidates, existing_action=None, existing_approval=None):
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
        elif "from actions" in stmt_str:
            result.scalar_one_or_none.return_value = existing_action
        elif "from approvals" in stmt_str:
            result.scalar_one_or_none.return_value = existing_approval
        elif "into actions" in stmt_str:
            # Simulate atomic insert returning new action
            fake_action = Action(
                id=uuid.uuid4(),
                case_id=case.id,
                intervention_id=candidates[0].id if candidates else uuid.uuid4(),
                status=ActionStatus.PLANNED if case.amount_at_risk_minor < 2000000 else ActionStatus.PENDING_APPROVAL,
                provider="demo",
                idempotency_key=f"action_{case.id}_{candidates[0].id if candidates else '1'}",
            )
            result.scalar_one_or_none.return_value = fake_action
        return result

    session.execute.side_effect = mock_execute
    return session


# ============================================================
# UNIT TESTS: POLICY ENFORCEMENT & ACTION CREATION
# ============================================================

@pytest.mark.asyncio
async def test_create_action_allow_auto(base_case, base_diagnosis, base_candidate):
    # Low-value case (â‚¹4,999.00) yields ALLOW_AUTO
    session = setup_mock_session(base_case, base_diagnosis, [base_candidate])

    resp = await create_action_for_case(session, base_case.id)

    assert resp.status == "created"
    assert resp.overall_outcome == "allow_auto"
    assert resp.selected_reason_code == "eligible_auto_execution"
    assert resp.action is not None
    assert resp.action.status == ActionStatus.PLANNED
    assert resp.action.approval is None
    assert base_case.status == CaseStatus.ACTION_PENDING
    assert session.add.call_count == 2  # 1 for POLICY_EVALUATED, 1 for ACTION_PLANNED


@pytest.mark.asyncio
async def test_create_action_require_approval(base_case, base_diagnosis, base_candidate):
    # High-value case (â‚¹75,000.00) yields REQUIRE_APPROVAL
    base_case.amount_at_risk_minor = 7_500_000
    base_candidate.recoverable_amount_minor = 7_500_000

    session = setup_mock_session(base_case, base_diagnosis, [base_candidate])

    resp = await create_action_for_case(session, base_case.id)

    assert resp.status == "created"
    assert resp.overall_outcome == "require_approval"
    assert resp.selected_reason_code == "high_value_approval_required"
    assert resp.action is not None
    assert resp.action.status == ActionStatus.PENDING_APPROVAL
    assert resp.action.approval is not None
    assert resp.action.approval.status == ApprovalStatus.PENDING
    assert base_case.status == CaseStatus.ACTION_PENDING
    assert session.add.call_count == 4  # POLICY_EVALUATED + Approval model + ACTION_PLANNED + APPROVAL_REQUESTED


@pytest.mark.asyncio
async def test_create_action_blocked_policy(base_case, base_diagnosis, base_candidate):
    # ERV <= 0 yields BLOCK
    base_candidate.expected_recovery_value_minor = -100
    session = setup_mock_session(base_case, base_diagnosis, [base_candidate])

    resp = await create_action_for_case(session, base_case.id)

    assert resp.status == "blocked"
    assert resp.overall_outcome == "block"
    assert resp.selected_reason_code == "no_eligible_candidate"
    assert resp.action is None
    assert base_case.status == CaseStatus.DETECTED  # Unchanged


@pytest.mark.asyncio
async def test_create_action_stopped_case_fails_closed(base_case, base_diagnosis, base_candidate):
    base_case.status = CaseStatus.STOPPED
    session = setup_mock_session(base_case, base_diagnosis, [base_candidate])

    with pytest.raises(StalePolicyAuthorizationError, match="status stopped"):
        await create_action_for_case(session, base_case.id)


@pytest.mark.asyncio
async def test_create_action_holdout_case_fails_closed(base_case, base_diagnosis, base_candidate):
    base_case.assignment_group = AssignmentGroup.HOLDOUT
    session = setup_mock_session(base_case, base_diagnosis, [base_candidate])

    with pytest.raises(StalePolicyAuthorizationError, match="not eligible"):
        await create_action_for_case(session, base_case.id)


@pytest.mark.asyncio
async def test_create_action_idempotent_existing(base_case, base_diagnosis, base_candidate):
    existing = Action(
        id=uuid.uuid4(),
        case_id=base_case.id,
        intervention_id=base_candidate.id,
        status=ActionStatus.PLANNED,
        provider="demo",
        idempotency_key=f"action_{base_case.id}_{base_candidate.id}",
    )
    session = setup_mock_session(base_case, base_diagnosis, [base_candidate], existing_action=existing)

    resp = await create_action_for_case(session, base_case.id)

    assert resp.status == "existing"
    assert resp.action is not None
    assert resp.action.id == existing.id


# ============================================================
# HUMAN APPROVAL WORKFLOW TESTS
# ============================================================

@pytest.mark.asyncio
async def test_decide_approval_approve_success(base_case, base_candidate):
    action = Action(
        id=uuid.uuid4(),
        case_id=base_case.id,
        intervention_id=base_candidate.id,
        status=ActionStatus.PENDING_APPROVAL,
        provider="demo",
        idempotency_key=f"action_{base_case.id}_{base_candidate.id}",
    )
    approval = Approval(
        id=uuid.uuid4(),
        action_id=action.id,
        case_id=base_case.id,
        status=ApprovalStatus.PENDING,
    )
    session = setup_mock_session(base_case, None, [base_candidate], existing_action=action, existing_approval=approval)

    resp = await decide_approval(
        session,
        action_id=action.id,
        decision="approve",
        approver_id="manager_john",
        decision_reason="Verified risk profile",
    )

    assert resp.status == ActionStatus.APPROVED
    assert resp.approval is not None
    assert resp.approval.status == ApprovalStatus.APPROVED
    assert resp.approval.approver_id == "manager_john"
    assert resp.approval.decision_reason == "Verified risk profile"
    assert base_case.status == CaseStatus.ACTION_APPROVED
    assert session.add.call_count == 1  # Audit event logged


@pytest.mark.asyncio
async def test_decide_approval_reject_success(base_case, base_candidate):
    action = Action(
        id=uuid.uuid4(),
        case_id=base_case.id,
        intervention_id=base_candidate.id,
        status=ActionStatus.PENDING_APPROVAL,
        provider="demo",
        idempotency_key=f"action_{base_case.id}_{base_candidate.id}",
    )
    approval = Approval(
        id=uuid.uuid4(),
        action_id=action.id,
        case_id=base_case.id,
        status=ApprovalStatus.PENDING,
    )
    session = setup_mock_session(base_case, None, [base_candidate], existing_action=action, existing_approval=approval)

    resp = await decide_approval(
        session,
        action_id=action.id,
        decision="reject",
        approver_id="manager_john",
        decision_reason="Customer requested no contact",
    )

    assert resp.status == ActionStatus.REJECTED
    assert resp.approval is not None
    assert resp.approval.status == ApprovalStatus.REJECTED
    assert base_case.status != CaseStatus.ACTION_APPROVED


@pytest.mark.asyncio
async def test_decide_approval_invalid_state_already_decided(base_case, base_candidate):
    action = Action(
        id=uuid.uuid4(),
        case_id=base_case.id,
        intervention_id=base_candidate.id,
        status=ActionStatus.APPROVED,
        provider="demo",
        idempotency_key=f"action_{base_case.id}_{base_candidate.id}",
    )
    approval = Approval(
        id=uuid.uuid4(),
        action_id=action.id,
        case_id=base_case.id,
        status=ApprovalStatus.APPROVED,
    )
    session = setup_mock_session(base_case, None, [base_candidate], existing_action=action, existing_approval=approval)

    with pytest.raises(InvalidApprovalStateError, match="expected 'pending'"):
        await decide_approval(session, action.id, "approve", "manager_john")


@pytest.mark.asyncio
async def test_decide_approval_invalid_decision_string(base_case, base_candidate):
    session = AsyncMock()
    with pytest.raises(InvalidApprovalStateError, match="Invalid approval decision"):
        await decide_approval(session, uuid.uuid4(), "invalid_cmd", "manager_john")
