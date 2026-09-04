import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.case import Case
from app.models.enums import AssignmentGroup, CaseStatus, ExperimentStatus
from app.models.experiment import Experiment
from app.models.experiment_assignment import ExperimentAssignment

logger = logging.getLogger(__name__)


class AssignmentError(Exception):
    pass


class TerminalCaseError(AssignmentError):
    """Raised when attempting to assign a terminal (STOPPED) case."""
    pass


class NoActiveExperimentError(AssignmentError):
    """Raised when no active experiment matches the criteria."""
    pass


def _deterministic_hash_assignment(experiment_id: uuid.UUID, case_id: uuid.UUID, holdout_percentage: int) -> Tuple[AssignmentGroup, str]:
    """Deterministically assign a case to TREATMENT or HOLDOUT based on a stable hash.

    Returns a tuple of (AssignmentGroup, hash_hex).
    """
    stable_string = f"{experiment_id}:{case_id}"
    hash_obj = hashlib.sha256(stable_string.encode("utf-8"))
    hash_hex = hash_obj.hexdigest()

    # Use the first 8 characters (32-bit int equivalent) for bucket assignment
    hash_int = int(hash_hex[:8], 16)

    # Map to 0-99 bucket
    bucket = hash_int % 100

    # If bucket < holdout_percentage, it's a holdout.
    if bucket < holdout_percentage:
        return AssignmentGroup.HOLDOUT, hash_hex

    return AssignmentGroup.TREATMENT, hash_hex


async def assign_experiment(session: AsyncSession, case: Case) -> ExperimentAssignment:
    """Assign a Case to the currently active Experiment deterministically.

    Must happen BEFORE any AI invocation.
    Idempotent: returns existing assignment if present.
    """

    # 1. Eligibility Check
    # Do not assign terminal cases to active recovery experiments.
    if case.status == CaseStatus.STOPPED:
        raise TerminalCaseError(f"Case {case.id} is STOPPED (terminal). Cannot assign to recovery experiment.")

    # 2. Select Active Experiment
    exp_stmt = select(Experiment).where(Experiment.status == ExperimentStatus.ACTIVE)
    exp_result = await session.execute(exp_stmt)
    active_experiments = exp_result.scalars().all()

    eligible_experiments = []
    for exp in active_experiments:
        # Check eligibility
        if not exp.segment_filter:
            eligible_experiments.append(exp)
            continue

        # Very simple deterministic segment matching for Phase 3
        # E.g. {"failure_category": "insufficient_funds"}
        is_match = True
        for key, expected_value in exp.segment_filter.items():
            if hasattr(case, key):
                actual_value = getattr(case, key)
                # handle UUID conversion safely for matching
                if isinstance(actual_value, uuid.UUID):
                    actual_value = str(actual_value)
                if actual_value != expected_value:
                    is_match = False
                    break
            else:
                # Key not found on Case, assume mismatch for strictness
                is_match = False
                break

        if is_match:
            eligible_experiments.append(exp)

    if not eligible_experiments:
        raise NoActiveExperimentError("No active experiment found for assignment.")

    # Deterministic precedence: sort by experiment ID string
    eligible_experiments.sort(key=lambda e: str(e.id))
    experiment = eligible_experiments[0]

    # 3. Check for existing assignment
    assignment_stmt = select(ExperimentAssignment).where(
        ExperimentAssignment.experiment_id == experiment.id,
        ExperimentAssignment.case_id == case.id
    )
    assignment_result = await session.execute(assignment_stmt)
    existing_assignment = assignment_result.scalar_one_or_none()

    if existing_assignment:
        logger.info(f"Idempotent assignment: Case {case.id} already assigned to {existing_assignment.group}")
        # Ensure Case reflects this assignment
        if case.assignment_group != existing_assignment.group:
            case.assignment_group = existing_assignment.group
            session.add(case)
        return existing_assignment

    # 4. Perform deterministic assignment
    assigned_group, hash_hex = _deterministic_hash_assignment(
        experiment.id, case.id, experiment.holdout_percentage
    )

    # 5. Persist assignment
    new_assignment = ExperimentAssignment(
        experiment_id=experiment.id,
        case_id=case.id,
        group=assigned_group,
        assignment_hash=hash_hex,
        assigned_at=datetime.now(timezone.utc)
    )
    session.add(new_assignment)

    # 6. Update Case State
    case.assignment_group = assigned_group

    # For a TREATMENT case, it simply remains DETECTED and moves to Phase 4 logically.
    # For a HOLDOUT case, no AI will process it.
    # We do NOT invoke AI here.
    session.add(case)

    return new_assignment
