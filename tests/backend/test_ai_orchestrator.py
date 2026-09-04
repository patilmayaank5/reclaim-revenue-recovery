import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from app.domain.ai.provider import (
    AINonRetryableError,
    AITransientError,
    FakeAIProvider,
)
from app.domain.ai.schemas import AIDiagnosisOutput
from app.models.ai_diagnosis import AIDiagnosis
from app.models.case import Case
from app.models.case_context import CaseContext
from app.models.enums import AssignmentGroup, CaseStatus
from app.services.ai_orchestrator import (
    AIEligibilityError,
    AIOrchestratorError,
    diagnose_case,
)


@pytest.fixture
def base_case():
    return Case(
        id=uuid.uuid4(),
        status=CaseStatus.DETECTED,
        amount_at_risk_minor=5000,
        currency="USD",
        failure_category="insufficient_funds",
        assignment_group=AssignmentGroup.TREATMENT
    )


@pytest.fixture
def base_context(base_case):
    return CaseContext(
        id=uuid.uuid4(),
        case_id=base_case.id,
        context_type="enrichment_baseline",
        context_data={
            "payment": {
                "failure_code": "fund_err",
                "failure_description": "NSF",
                "secret_key": "DO_NOT_SEND"
            },
            "merchant": {
                "business_type": "saas"
            }
        }
    )


def setup_mock_session(case, context, existing_diagnosis=None, fail_on_commit=False):
    session = AsyncMock()

    ai_diagnoses_calls = 0

    async def mock_execute(stmt):
        nonlocal ai_diagnoses_calls
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from cases" in stmt_str:
            result.scalar_one_or_none.return_value = case
        elif "from case_contexts" in stmt_str:
            result.scalar_one_or_none.return_value = context
        elif "from ai_diagnoses" in stmt_str:
            if ai_diagnoses_calls == 0 and fail_on_commit:
                # If fail_on_commit is True, we want to simulate the race condition,
                # meaning it DOES NOT exist initially.
                result.scalar_one_or_none.return_value = None
            else:
                result.scalar_one_or_none.return_value = existing_diagnosis
                result.scalar_one.return_value = existing_diagnosis

            ai_diagnoses_calls += 1
        return result

    session.execute.side_effect = mock_execute

    if fail_on_commit:
        session.commit.side_effect = IntegrityError("test", "test", "test")

    return session


@pytest.mark.asyncio
async def test_treatment_gate_invokes_provider(base_case, base_context):
    session = setup_mock_session(base_case, base_context)
    provider = FakeAIProvider()

    diagnosis = await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 1
    assert diagnosis.diagnosis_category == "insufficient_funds"

    # Verify input contract (integer minor units, allowlist, no secrets)
    payload = provider.last_payload
    assert payload["amount_at_risk_minor"] == 5000
    assert payload["currency"] == "USD"
    assert payload["failure_code"] == "fund_err"
    assert "secret_key" not in payload


@pytest.mark.asyncio
async def test_holdout_gate_blocks_provider(base_case, base_context):
    base_case.assignment_group = AssignmentGroup.HOLDOUT
    session = setup_mock_session(base_case, base_context)
    provider = FakeAIProvider()

    with pytest.raises(AIEligibilityError):
        await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 0


@pytest.mark.asyncio
async def test_stopped_gate_blocks_provider(base_case, base_context):
    base_case.status = CaseStatus.STOPPED
    session = setup_mock_session(base_case, base_context)
    provider = FakeAIProvider()

    with pytest.raises(AIEligibilityError):
        await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 0


@pytest.mark.asyncio
async def test_unassigned_gate_blocks_provider(base_case, base_context):
    base_case.assignment_group = None
    session = setup_mock_session(base_case, base_context)
    provider = FakeAIProvider()

    with pytest.raises(AIEligibilityError):
        await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 0


@pytest.mark.asyncio
async def test_ai_orchestrator_transient_retry(base_case, base_context):
    session = setup_mock_session(base_case, base_context)

    class RetryProvider(FakeAIProvider):
        async def diagnose(self, payload):
            self.call_count += 1
            if self.call_count < 2:
                raise AITransientError("rate limit")
            return await super().diagnose(payload)

    provider = RetryProvider()

    diagnosis = await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 3
    assert diagnosis.diagnosis_category == "insufficient_funds"


@pytest.mark.asyncio
async def test_ai_orchestrator_transient_retry_max(base_case, base_context):
    session = setup_mock_session(base_case, base_context)

    class MaxRetryProvider(FakeAIProvider):
        async def diagnose(self, payload):
            self.call_count += 1
            raise AITransientError("rate limit")

    provider = MaxRetryProvider()

    with pytest.raises(AIOrchestratorError, match="failed after max transient retries"):
        await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 2 # Max retries


@pytest.mark.asyncio
async def test_ai_orchestrator_non_retryable_error(base_case, base_context):
    session = setup_mock_session(base_case, base_context)
    provider = FakeAIProvider(should_fail_permanent=True)

    with pytest.raises(AIOrchestratorError, match="permanently"):
        await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 1 # No retry


@pytest.mark.asyncio
async def test_ai_orchestrator_idempotency(base_case, base_context):
    existing = AIDiagnosis(id=uuid.uuid4(), case_id=base_case.id, diagnosis_category="fraud")
    session = setup_mock_session(base_case, base_context, existing_diagnosis=existing)
    provider = FakeAIProvider()

    diagnosis = await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 0
    assert diagnosis is existing


@pytest.mark.asyncio
async def test_ai_orchestrator_concurrent_race(base_case, base_context):
    existing = AIDiagnosis(id=uuid.uuid4(), case_id=base_case.id, diagnosis_category="fraud")
    # Simulate the DB unique constraint firing (IntegrityError) during commit
    session = setup_mock_session(base_case, base_context, existing_diagnosis=existing, fail_on_commit=True)
    provider = FakeAIProvider()

    diagnosis = await diagnose_case(session, base_case.id, provider)

    assert provider.call_count == 1
    # We should get the existing one returned rather than an unhandled IntegrityError
    assert diagnosis is existing


def test_schema_validation():
    # Valid
    valid = AIDiagnosisOutput(
        diagnosis_category="insufficient_funds",
        reason="Test",
        ai_confidence=0.9,
        recovery_probability=0.5,
        evidence={},
        uncertainty="None"
    )
    assert valid.diagnosis_category.value == "insufficient_funds"

    # Invalid Enum
    with pytest.raises(ValidationError):
        AIDiagnosisOutput(
            diagnosis_category="invalid_garbage_category",
            reason="Test",
            ai_confidence=0.9,
            evidence={},
            uncertainty="None"
        )

    # Invalid confidence bounds
    with pytest.raises(ValidationError):
        AIDiagnosisOutput(
            diagnosis_category="insufficient_funds",
            reason="Test",
            ai_confidence=1.5, # > 1.0
            evidence={},
            uncertainty="None"
        )
