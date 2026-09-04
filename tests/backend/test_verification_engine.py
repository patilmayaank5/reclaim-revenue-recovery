import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.providers.base import VerificationRequest, VerificationResponse
from app.domain.providers.simulator import SimulatorProvider
from app.models.action import Action
from app.models.case import Case
from app.models.enums import (
    ActionStatus,
    AssignmentGroup,
    AuditEventType,
    CaseStatus,
    PaymentStatus,
    VerificationStatus,
)
from app.models.intervention import Intervention
from app.models.payment import Payment
from app.models.verification import Verification
from app.services.verification_service import ActionNotVerifiableError, verify_action


# ============================================================
# FIXTURES & MOCK SESSION SETUP
# ============================================================

@pytest.fixture
def base_payment():
    return Payment(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        external_id="pay_test_verif_001",
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
        status=CaseStatus.ACTION_EXECUTED,
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
        status=ActionStatus.EXECUTED,
        provider="simulator",
        idempotency_key=f"action_{base_case.id}_{base_intervention.id}",
        execution_metadata={"execution_outcome": "success", "provider_transaction_id": "sim_tx_123"},
    )


def setup_verification_mock_session(case, action, intervention, payment, existing_verification=None):
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
        elif "from payments" in stmt_str:
            result.scalar_one_or_none.return_value = payment
            result.scalar_one.return_value = payment
        elif "from interventions" in stmt_str:
            result.scalar_one_or_none.return_value = intervention
            result.scalar_one.return_value = intervention
        elif "from verifications" in stmt_str:
            result.scalar_one_or_none.return_value = existing_verification
            result.scalar_one.return_value = existing_verification
        return result

    session.execute.side_effect = mock_execute
    return session


# ============================================================
# PHASE 9 TESTS: VERIFICATION & PAYMENT STATUS RULES
# ============================================================

@pytest.mark.asyncio
async def test_1_2_verify_executed_action_recovered_updates_payment_status(base_case, base_action, base_intervention, base_payment):
    """Scenario 1 & 2: Executed action verified recovered transitions PaymentStatus to CAPTURED."""
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    resp = await verify_action(session, base_action.id, verification_scenario="recovered")

    assert resp.status == VerificationStatus.VERIFIED_RECOVERED
    assert resp.recovered_amount_minor == 499_900
    assert base_payment.status == PaymentStatus.CAPTURED
    assert base_case.status == CaseStatus.RECOVERED
    assert base_action.status == ActionStatus.EXECUTED


@pytest.mark.asyncio
async def test_3_6_verify_executed_action_not_recovered_preserves_payment_and_action_status(base_case, base_action, base_intervention, base_payment):
    """Scenario 3 & 6: NOT_RECOVERED keeps PaymentStatus FAILED and ActionStatus EXECUTED."""
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    resp = await verify_action(session, base_action.id, verification_scenario="not_recovered")

    assert resp.status == VerificationStatus.VERIFIED_NOT_RECOVERED
    assert base_payment.status == PaymentStatus.FAILED  # Strictly UNCHANGED
    assert base_case.status == CaseStatus.NOT_RECOVERED
    assert base_action.status == ActionStatus.EXECUTED


@pytest.mark.asyncio
async def test_4_verify_pending_does_not_mutate_payment_status(base_case, base_action, base_intervention, base_payment):
    """Scenario 4: PENDING verification does not mutate PaymentStatus."""
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    resp = await verify_action(session, base_action.id, verification_scenario="pending")

    assert resp.status == VerificationStatus.PENDING
    assert base_payment.status == PaymentStatus.FAILED
    assert base_case.status == CaseStatus.VERIFYING


@pytest.mark.asyncio
async def test_5_verification_failure_does_not_mutate_payment_status(base_case, base_action, base_intervention, base_payment):
    """Scenario 5: VERIFICATION_FAILED does not mutate PaymentStatus."""
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    resp = await verify_action(session, base_action.id, verification_scenario="verification_failed")

    assert resp.status == VerificationStatus.VERIFICATION_FAILED
    assert base_payment.status == PaymentStatus.FAILED


# ============================================================
# PHASE 9 TESTS: AMBIGUOUS TIMEOUT SAFETY (NO SECOND EXECUTION)
# ============================================================

@pytest.mark.asyncio
async def test_7_8_9_ambiguous_executing_action_verified_recovered_no_reexecution(base_case, base_action, base_intervention, base_payment):
    """Scenario 7, 8 & 9: Ambiguous EXECUTING action verified recovered transitions to CAPTURED without re-execution."""
    base_action.status = ActionStatus.EXECUTING
    base_action.execution_metadata = {"ambiguous": True, "requires_verification": True}
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    resp = await verify_action(session, base_action.id, verification_scenario="recovered")

    assert resp.status == VerificationStatus.VERIFIED_RECOVERED
    assert base_payment.status == PaymentStatus.CAPTURED
    assert base_case.status == CaseStatus.RECOVERED
    assert base_action.status == ActionStatus.EXECUTED  # Cleared ambiguous executing


@pytest.mark.asyncio
async def test_10_ambiguous_pending_remains_executing_verifying(base_case, base_action, base_intervention, base_payment):
    """Scenario 10: Ambiguous EXECUTING action verified pending remains EXECUTING with verification required."""
    base_action.status = ActionStatus.EXECUTING
    base_action.execution_metadata = {"ambiguous": True, "requires_verification": True}
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    resp = await verify_action(session, base_action.id, verification_scenario="pending")

    assert resp.status == VerificationStatus.PENDING
    assert base_payment.status == PaymentStatus.FAILED
    assert base_action.status == ActionStatus.EXECUTING
    assert base_action.execution_metadata["ambiguous"] is True


@pytest.mark.asyncio
async def test_11_ambiguous_not_recovered_transitions_to_failed(base_case, base_action, base_intervention, base_payment):
    """Scenario 11: Ambiguous EXECUTING action verified not_recovered transitions to FAILED safely."""
    base_action.status = ActionStatus.EXECUTING
    base_action.execution_metadata = {"ambiguous": True, "requires_verification": True}
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    resp = await verify_action(session, base_action.id, verification_scenario="not_recovered")

    assert resp.status == VerificationStatus.VERIFIED_NOT_RECOVERED
    assert base_payment.status == PaymentStatus.FAILED
    assert base_case.status == CaseStatus.NOT_RECOVERED
    assert base_action.status == ActionStatus.FAILED


# ============================================================
# PHASE 9 TESTS: IDEMPOTENCY, CONCURRENCY & AUDIT
# ============================================================

@pytest.mark.asyncio
async def test_12_13_14_duplicate_verification_is_idempotent(base_case, base_action, base_intervention, base_payment):
    """Scenario 12, 13 & 14: Repeated verification returns existing canonical result without duplicate mutations or events."""
    existing_verif = Verification(
        id=uuid.uuid4(),
        action_id=base_action.id,
        case_id=base_case.id,
        payment_id=base_payment.id,
        status=VerificationStatus.VERIFIED_RECOVERED,
        observed_payment_status="captured",
        recovered_amount_minor=499_900,
        currency="INR",
    )
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment, existing_verification=existing_verif)

    resp = await verify_action(session, base_action.id)

    assert resp.id == existing_verif.id
    assert resp.status == VerificationStatus.VERIFIED_RECOVERED
    # Assert Step 2 provider call was bypassed completely
    assert session.add.call_count == 0


@pytest.mark.asyncio
async def test_16_17_18_audit_event_and_normalized_metadata(base_case, base_action, base_intervention, base_payment):
    """Scenario 16, 17 & 18: VERIFICATION_COMPLETED audit event contains normalized allowlisted fields."""
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    await verify_action(session, base_action.id, verification_scenario="recovered")

    assert session.add.call_count == 2
    audit = session.add.call_args_list[1][0][0]
    assert audit.event_type == AuditEventType.VERIFICATION_COMPLETED
    assert audit.event_data["verification_status"] == "verified_recovered"
    assert audit.event_data["provider"] == "simulator"
    # Ensure no secrets or raw headers are present
    assert "authorization" not in audit.event_data
    assert "api_key" not in audit.event_data


# ============================================================
# PHASE 9 TESTS: ELIGIBILITY & INELIGIBLE ACTION STATES
# ============================================================

@pytest.mark.asyncio
async def test_19_ineligible_action_planned_rejected(base_case, base_action, base_intervention, base_payment):
    """Scenario 19: PLANNED action rejected for verification."""
    base_action.status = ActionStatus.PLANNED
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    with pytest.raises(ActionNotVerifiableError, match="Must be executed or ambiguous executing"):
        await verify_action(session, base_action.id)


@pytest.mark.asyncio
async def test_19_ineligible_action_failed_rejected(base_case, base_action, base_intervention, base_payment):
    """Scenario 19: FAILED action rejected for verification."""
    base_action.status = ActionStatus.FAILED
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    with pytest.raises(ActionNotVerifiableError, match="Must be executed or ambiguous executing"):
        await verify_action(session, base_action.id)


@pytest.mark.asyncio
async def test_19_ineligible_active_executing_rejected(base_case, base_action, base_intervention, base_payment):
    """Scenario 19: Active EXECUTING (non-ambiguous) action rejected for verification."""
    base_action.status = ActionStatus.EXECUTING
    base_action.execution_metadata = {"ambiguous": False}
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    with pytest.raises(ActionNotVerifiableError, match="before completion or timeout"):
        await verify_action(session, base_action.id)


@pytest.mark.asyncio
async def test_21_manual_review_intervention_rejected(base_case, base_action, base_intervention, base_payment):
    """Scenario 21: manual_review intervention cannot be verified."""
    base_intervention.intervention_type = "manual_review"
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    with pytest.raises(ActionNotVerifiableError, match="cannot be verified as payment execution"):
        await verify_action(session, base_action.id)


@pytest.mark.asyncio
async def test_22_simulator_verification_is_deterministic():
    """Scenario 22: SimulatorProvider.verify is 100% deterministic."""
    provider = SimulatorProvider()
    req = VerificationRequest(
        action_id=uuid.uuid4(),
        case_id=uuid.uuid4(),
        payment_id=uuid.uuid4(),
        provider="simulator",
        intervention_type="smart_retry",
        amount_minor=1000,
        currency="INR",
        metadata={"verification_scenario": "recovered"},
    )
    res = await provider.verify(req)
    assert res.status == VerificationStatus.VERIFIED_RECOVERED
    assert res.observed_payment_status == "captured"
    assert res.recovered_amount_minor == 1000


# ============================================================
# TARGETED REGRESSION TESTS: CONCURRENCY & TERMINAL PROTECTION
# ============================================================

@pytest.mark.asyncio
async def test_bug1_in_flight_verifying_case_rejected(base_case, base_action, base_intervention, base_payment):
    """Bug 1 Fix: Second verification request rejected with ActionNotVerifiableError when Case is VERIFYING."""
    base_case.status = CaseStatus.VERIFYING
    session = setup_verification_mock_session(base_case, base_action, base_intervention, base_payment)

    with pytest.raises(ActionNotVerifiableError, match="Verification is already in progress"):
        await verify_action(session, base_action.id)


@pytest.mark.asyncio
async def test_bug2_terminal_recovered_cannot_be_overwritten_by_pending(base_case, base_action, base_intervention, base_payment):
    """Bug 2 Fix: Stale request returning PENDING does NOT overwrite existing VERIFIED_RECOVERED record or CAPTURED payment."""
    existing_verif = Verification(
        id=uuid.uuid4(),
        action_id=base_action.id,
        case_id=base_case.id,
        payment_id=base_payment.id,
        status=VerificationStatus.VERIFIED_RECOVERED,
        observed_payment_status="captured",
        recovered_amount_minor=499_900,
        currency="INR",
    )
    base_payment.status = PaymentStatus.CAPTURED
    base_case.status = CaseStatus.RECOVERED

    session = setup_verification_mock_session(
        base_case, base_action, base_intervention, base_payment, existing_verification=existing_verif
    )

    resp = await verify_action(session, base_action.id, verification_scenario="pending")

    assert resp.status == VerificationStatus.VERIFIED_RECOVERED
    assert base_payment.status == PaymentStatus.CAPTURED
    assert base_case.status == CaseStatus.RECOVERED


@pytest.mark.asyncio
async def test_bug2_terminal_recovered_cannot_be_overwritten_by_failed(base_case, base_action, base_intervention, base_payment):
    """Bug 2 Fix: Stale request returning VERIFICATION_FAILED does NOT overwrite existing VERIFIED_RECOVERED record."""
    existing_verif = Verification(
        id=uuid.uuid4(),
        action_id=base_action.id,
        case_id=base_case.id,
        payment_id=base_payment.id,
        status=VerificationStatus.VERIFIED_RECOVERED,
        observed_payment_status="captured",
        recovered_amount_minor=499_900,
        currency="INR",
    )
    base_payment.status = PaymentStatus.CAPTURED
    base_case.status = CaseStatus.RECOVERED

    session = setup_verification_mock_session(
        base_case, base_action, base_intervention, base_payment, existing_verification=existing_verif
    )

    resp = await verify_action(session, base_action.id, verification_scenario="verification_failed")

    assert resp.status == VerificationStatus.VERIFIED_RECOVERED
    assert base_payment.status == PaymentStatus.CAPTURED


@pytest.mark.asyncio
async def test_bug2_terminal_not_recovered_cannot_be_overwritten_by_pending(base_case, base_action, base_intervention, base_payment):
    """Bug 2 Fix: Stale request returning PENDING does NOT overwrite existing VERIFIED_NOT_RECOVERED record."""
    existing_verif = Verification(
        id=uuid.uuid4(),
        action_id=base_action.id,
        case_id=base_case.id,
        payment_id=base_payment.id,
        status=VerificationStatus.VERIFIED_NOT_RECOVERED,
        observed_payment_status="failed",
        recovered_amount_minor=None,
        currency="INR",
    )
    base_payment.status = PaymentStatus.FAILED
    base_case.status = CaseStatus.NOT_RECOVERED

    session = setup_verification_mock_session(
        base_case, base_action, base_intervention, base_payment, existing_verification=existing_verif
    )

    resp = await verify_action(session, base_action.id, verification_scenario="pending")

    assert resp.status == VerificationStatus.VERIFIED_NOT_RECOVERED
    assert base_payment.status == PaymentStatus.FAILED
    assert base_case.status == CaseStatus.NOT_RECOVERED


def test_bug3_verification_model_has_action_id_unique_constraint():
    """Bug 3 Fix: Verification model defines uq_verifications_action_id UniqueConstraint."""
    constraints = [
        c for c in Verification.__table_args__
        if hasattr(c, "name") and c.name == "uq_verifications_action_id"
    ]
    assert len(constraints) == 1
    assert "action_id" in [col.name for col in constraints[0].columns]
