import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.providers.base import ExecutionRequest, ExecutionResponse, ExecutionResultStatus
from app.domain.providers.simulator import SimulatorProvider
from app.models.action import Action
from app.models.case import Case
from app.models.enums import ActionStatus, AssignmentGroup, AuditEventType, CaseStatus, PaymentStatus
from app.models.intervention import Intervention
from app.models.payment import Payment
from app.services.execution_service import ActionNotExecutableError, execute_action


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def base_payment():
    return Payment(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        external_id="pay_test_001",
        amount_minor=499_900,
        currency="INR",
        status=PaymentStatus.FAILED,
        provider="demo",
        attempted_at=MagicMock(),
    )


@pytest.fixture
def base_case(base_payment):
    return Case(
        id=uuid.uuid4(),
        merchant_id=base_payment.merchant_id,
        payment_id=base_payment.id,
        status=CaseStatus.ACTION_PENDING,
        assignment_group=AssignmentGroup.TREATMENT,
        amount_at_risk_minor=499_900,
        currency="INR",
    )


@pytest.fixture
def base_intervention(base_case):
    return Intervention(
        id=uuid.uuid4(),
        case_id=base_case.id,
        intervention_type="smart_retry",
        recoverable_amount_minor=499_900,
        currency="INR",
        estimated_recovery_probability_bps=6500,
        intervention_cost_minor=5,
        risk_penalty_minor=10,
        expected_recovery_value_minor=324915,
        rank=1,
    )


@pytest.fixture
def base_action(base_case, base_intervention):
    return Action(
        id=uuid.uuid4(),
        case_id=base_case.id,
        intervention_id=base_intervention.id,
        status=ActionStatus.PLANNED,
        provider="simulator",
        idempotency_key=f"action_{base_case.id}_{base_intervention.id}",
    )


def setup_execution_mock_session(case, action, intervention, payment=None):
    session = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()

        if "from actions" in stmt_str:
            result.scalar_one_or_none.return_value = action
            result.scalar_one.return_value = action
        elif "from cases" in stmt_str:
            result.scalar_one_or_none.return_value = case
            result.scalar_one.return_value = case
        elif "from interventions" in stmt_str:
            result.scalar_one_or_none.return_value = intervention
            result.scalar_one.return_value = intervention
        elif "from approvals" in stmt_str:
            result.scalar_one_or_none.return_value = None
        return result

    session.execute.side_effect = mock_execute
    return session


# ============================================================
# UNIT TESTS: ELIGIBILITY & AUTHORIZATION BOUNDARY
# ============================================================

@pytest.mark.asyncio
async def test_execute_planned_action_success(base_case, base_action, base_intervention, base_payment):
    session = setup_execution_mock_session(base_case, base_action, base_intervention, base_payment)

    resp = await execute_action(session, base_action.id, provider_name="simulator")

    assert resp.status == ActionStatus.EXECUTED
    assert resp.executed_at is not None
    assert resp.execution_metadata["execution_outcome"] == "success"
    assert resp.execution_metadata["requires_verification"] is False
    assert base_case.status == CaseStatus.ACTION_EXECUTED
    assert base_payment.status == PaymentStatus.FAILED  # PaymentStatus strictly unchanged by Phase 8


@pytest.mark.asyncio
async def test_execute_approved_action_success(base_case, base_action, base_intervention):
    base_action.status = ActionStatus.APPROVED
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    resp = await execute_action(session, base_action.id, provider_name="simulator")

    assert resp.status == ActionStatus.EXECUTED
    assert resp.executed_at is not None
    assert base_case.status == CaseStatus.ACTION_EXECUTED


@pytest.mark.asyncio
async def test_execute_pending_approval_rejected(base_case, base_action, base_intervention):
    base_action.status = ActionStatus.PENDING_APPROVAL
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    with pytest.raises(ActionNotExecutableError, match="Must be 'planned' or 'approved'"):
        await execute_action(session, base_action.id)


@pytest.mark.asyncio
async def test_execute_rejected_action_rejected(base_case, base_action, base_intervention):
    base_action.status = ActionStatus.REJECTED
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    with pytest.raises(ActionNotExecutableError, match="Must be 'planned' or 'approved'"):
        await execute_action(session, base_action.id)


@pytest.mark.asyncio
async def test_execute_already_executed_action_rejected(base_case, base_action, base_intervention):
    base_action.status = ActionStatus.EXECUTED
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    with pytest.raises(ActionNotExecutableError, match="Must be 'planned' or 'approved'"):
        await execute_action(session, base_action.id)


@pytest.mark.asyncio
async def test_execute_manual_review_intervention_rejected(base_case, base_action, base_intervention):
    base_intervention.intervention_type = "manual_review"
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    with pytest.raises(ActionNotExecutableError, match="cannot be executed automatically"):
        await execute_action(session, base_action.id)


@pytest.mark.asyncio
async def test_execute_stopped_case_rejected(base_case, base_action, base_intervention):
    base_case.status = CaseStatus.STOPPED
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    with pytest.raises(ActionNotExecutableError, match="case in status 'stopped'"):
        await execute_action(session, base_action.id)


@pytest.mark.asyncio
async def test_execute_holdout_case_rejected(base_case, base_action, base_intervention):
    base_case.assignment_group = AssignmentGroup.HOLDOUT
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    with pytest.raises(ActionNotExecutableError, match="ineligible for execution"):
        await execute_action(session, base_action.id)


# ============================================================
# SIMULATOR SCENARIOS & AMBIGUOUS TIMEOUT TESTS
# ============================================================

@pytest.mark.asyncio
async def test_simulator_permanent_failure(base_case, base_action, base_intervention):
    base_action.execution_metadata = {"simulator_scenario": "permanent_failure"}
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    resp = await execute_action(session, base_action.id, provider_name="simulator")

    assert resp.status == ActionStatus.FAILED
    assert resp.executed_at is not None
    assert resp.execution_metadata["execution_outcome"] == "permanent_failure"
    assert resp.execution_metadata["error_code"] == "SIM_400_CARD_EXPIRED"
    assert base_case.status == CaseStatus.ACTION_EXECUTED


@pytest.mark.asyncio
async def test_simulator_transient_failure(base_case, base_action, base_intervention):
    base_action.execution_metadata = {"simulator_scenario": "transient_failure"}
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    resp = await execute_action(session, base_action.id, provider_name="simulator")

    assert resp.status == ActionStatus.FAILED
    assert resp.executed_at is not None
    assert resp.execution_metadata["execution_outcome"] == "transient_failure"
    assert resp.execution_metadata["error_code"] == "SIM_503_SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_simulator_ambiguous_timeout(base_case, base_action, base_intervention):
    base_action.execution_metadata = {"simulator_scenario": "timeout"}
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    resp = await execute_action(session, base_action.id, provider_name="simulator")

    # Retains EXECUTING status for Phase 9 verification
    assert resp.status == ActionStatus.EXECUTING
    assert resp.executed_at is None
    assert resp.execution_metadata["execution_outcome"] == "ambiguous_timeout"
    assert resp.execution_metadata["requires_verification"] is True
    assert resp.execution_metadata["ambiguous"] is True

    # Verify a second execution attempt on ambiguous action is rejected
    with pytest.raises(ActionNotExecutableError, match="Ambiguous timeouts require Phase 9 verification"):
        await execute_action(session, base_action.id)


@pytest.mark.asyncio
async def test_simulator_provider_direct():
    provider = SimulatorProvider()
    req = ExecutionRequest(
        action_id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        amount_minor=1000,
        currency="INR",
        intervention_type="smart_retry",
        idempotency_key="key_123",
        metadata={"simulator_scenario": "success"},
    )
    res = await provider.execute(req)
    assert res.status == ExecutionResultStatus.SUCCESS
    assert res.provider_transaction_id == "sim_tx_key_123"
    assert res.requires_verification is False


@pytest.mark.asyncio
async def test_audit_event_emitted_on_execution(base_case, base_action, base_intervention):
    session = setup_execution_mock_session(base_case, base_action, base_intervention)

    await execute_action(session, base_action.id, provider_name="simulator")

    # Step 3 commits audit event
    assert session.add.call_count == 1
    audit = session.add.call_args[0][0]
    assert audit.event_type == AuditEventType.ACTION_EXECUTED
    assert audit.event_data["execution_outcome"] == "success"
    assert audit.event_data["provider"] == "simulator"
