import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.case import Case
from app.models.enums import AssignmentGroup, CaseStatus, ExperimentStatus
from app.models.experiment import Experiment
from app.models.experiment_assignment import ExperimentAssignment
from app.services.experiment_assignment import (
    NoActiveExperimentError,
    TerminalCaseError,
    _deterministic_hash_assignment,
    assign_experiment,
)


def test_deterministic_hash_assignment():
    exp_id = uuid.uuid4()
    case_id = uuid.uuid4()

    # Same inputs should produce exactly the same group
    group1, hash1 = _deterministic_hash_assignment(exp_id, case_id, 50)
    group2, hash2 = _deterministic_hash_assignment(exp_id, case_id, 50)

    assert group1 == group2
    assert hash1 == hash2

    # With holdout_percentage = 0, should always be TREATMENT
    g, _ = _deterministic_hash_assignment(exp_id, case_id, 0)
    assert g == AssignmentGroup.TREATMENT

    # With holdout_percentage = 100, should always be HOLDOUT
    g, _ = _deterministic_hash_assignment(exp_id, case_id, 100)
    assert g == AssignmentGroup.HOLDOUT


@pytest.fixture
def assignment_data():
    exp = Experiment(
        id=uuid.uuid4(),
        status=ExperimentStatus.ACTIVE,
        holdout_percentage=50
    )
    case = Case(
        id=uuid.uuid4(),
        status=CaseStatus.DETECTED
    )
    return exp, case


@pytest.mark.asyncio
async def test_assign_experiment_matching_and_consistency(assignment_data):
    exp, case = assignment_data
    exp.segment_filter = {"failure_category": "insufficient_funds"}
    case.failure_category = "insufficient_funds"

    session = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from experiments" in stmt_str:
            result.scalars().all.return_value = [exp]
        elif "from experiment_assignments" in stmt_str:
            result.scalar_one_or_none.return_value = None
        return result

    session.execute.side_effect = mock_execute

    assignment = await assign_experiment(session, case)

    assert assignment.experiment_id == exp.id
    # Test Consistency: Case assignment group matches ExperimentAssignment
    assert case.assignment_group == assignment.group


@pytest.mark.asyncio
async def test_assign_experiment_non_matching_ignored(assignment_data):
    exp, case = assignment_data
    exp.segment_filter = {"failure_category": "fraud"}
    case.failure_category = "insufficient_funds"

    session = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from experiments" in stmt_str:
            result.scalars().all.return_value = [exp]
        return result

    session.execute.side_effect = mock_execute

    with pytest.raises(NoActiveExperimentError):
        await assign_experiment(session, case)


@pytest.mark.asyncio
async def test_assign_experiment_multiple_deterministic_precedence(assignment_data):
    exp1, case = assignment_data
    exp2 = Experiment(
        id=uuid.uuid4(),
        status=ExperimentStatus.ACTIVE,
        holdout_percentage=50,
        segment_filter=None
    )

    # We want to ensure it sorts by string ID. Let's make sure exp1's string is greater than exp2's
    if str(exp1.id) < str(exp2.id):
        exp1, exp2 = exp2, exp1 # Now exp2 has smaller ID string, so it should be picked first

    session = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from experiments" in stmt_str:
            # DB might return them in any order
            result.scalars().all.return_value = [exp1, exp2]
        elif "from experiment_assignments" in stmt_str:
            result.scalar_one_or_none.return_value = None
        return result

    session.execute.side_effect = mock_execute

    assignment = await assign_experiment(session, case)

    # The one with the "smaller" UUID string should be picked
    assert str(assignment.experiment_id) == min(str(exp1.id), str(exp2.id))



@pytest.mark.asyncio
async def test_assign_experiment_terminal_case(assignment_data):
    exp, case = assignment_data
    case.status = CaseStatus.STOPPED

    session = AsyncMock()
    with pytest.raises(TerminalCaseError):
        await assign_experiment(session, case)


@pytest.mark.asyncio
async def test_assign_experiment_no_active(assignment_data):
    exp, case = assignment_data
    session = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        result.scalars().all.return_value = []
        return result

    session.execute.side_effect = mock_execute

    with pytest.raises(NoActiveExperimentError):
        await assign_experiment(session, case)


@pytest.mark.asyncio
async def test_assign_experiment_idempotent(assignment_data):
    exp, case = assignment_data
    session = AsyncMock()

    existing_assignment = ExperimentAssignment(
        id=uuid.uuid4(),
        experiment_id=exp.id,
        case_id=case.id,
        group=AssignmentGroup.HOLDOUT,
        assignment_hash="fakehash",
        assigned_at=datetime.now(timezone.utc)
    )

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from experiments" in stmt_str:
            result.scalars().all.return_value = [exp]
        elif "from experiment_assignments" in stmt_str:
            result.scalar_one_or_none.return_value = existing_assignment
        return result

    session.execute.side_effect = mock_execute

    assignment = await assign_experiment(session, case)

    assert assignment is existing_assignment
    assert case.assignment_group == AssignmentGroup.HOLDOUT
    assert session.add.called  # Only called for updating the case
