import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.case import Case
from app.models.ai_diagnosis import AIDiagnosis
from app.models.intervention import Intervention
from app.models.enums import CaseStatus, AssignmentGroup
from app.services.intervention_orchestrator import generate_and_rank_candidates, InterventionGenerationError

@pytest.fixture
def base_case():
    return Case(
        id=uuid.uuid4(),
        status=CaseStatus.DETECTED,
        assignment_group=AssignmentGroup.TREATMENT,
        amount_at_risk_minor=10000,
        currency="INR"
    )

@pytest.fixture
def base_diagnosis(base_case):
    return AIDiagnosis(
        id=uuid.uuid4(),
        case_id=base_case.id,
        diagnosis_category="insufficient_funds",
        recovery_probability=0.65
    )

def setup_mock_session(case, diagnosis):
    session = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from cases" in stmt_str:
            result.scalar_one_or_none.return_value = case
        elif "from ai_diagnoses" in stmt_str:
            result.scalar_one_or_none.return_value = diagnosis
        elif "into interventions" in stmt_str or "on conflict" in stmt_str:
            # For the upsert statement
            fake_intervention = Intervention(
                id=uuid.uuid4(),
                case_id=case.id,
                intervention_type="mock",
                expected_recovery_value_minor=100
            )
            result.scalar_one.return_value = fake_intervention
        return result

    session.execute.side_effect = mock_execute
    return session


@pytest.mark.asyncio
async def test_generator_blocks_stopped(base_case, base_diagnosis):
    base_case.status = CaseStatus.STOPPED
    session = setup_mock_session(base_case, base_diagnosis)
    res = await generate_and_rank_candidates(session, base_case.id)
    assert len(res) == 0

@pytest.mark.asyncio
async def test_generator_blocks_holdout(base_case, base_diagnosis):
    base_case.assignment_group = AssignmentGroup.HOLDOUT
    session = setup_mock_session(base_case, base_diagnosis)
    res = await generate_and_rank_candidates(session, base_case.id)
    assert len(res) == 0

@pytest.mark.asyncio
async def test_generator_missing_diagnosis(base_case):
    session = setup_mock_session(base_case, None)
    with pytest.raises(InterventionGenerationError, match="Missing AIDiagnosis"):
        await generate_and_rank_candidates(session, base_case.id)

@pytest.mark.asyncio
async def test_generator_success_generates_candidates(base_case, base_diagnosis):
    session = setup_mock_session(base_case, base_diagnosis)
    res = await generate_and_rank_candidates(session, base_case.id)
    # insufficient_funds maps to 4 types
    assert len(res) == 4
    # All are fake interventions returned by mock, but we know it attempted 4 upserts
    # Let's count session.execute calls. 1 for case, 1 for diagnosis, 4 for upserts.
    assert session.execute.call_count == 6
