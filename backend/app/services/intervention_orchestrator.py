import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.case import Case
from app.models.ai_diagnosis import AIDiagnosis
from app.models.intervention import Intervention
from app.models.enums import CaseStatus, AssignmentGroup

from app.domain.interventions.schemas import InterventionType, ERVCalculationParams, CalibrationInput
from app.domain.interventions.generator import get_applicable_interventions
from app.domain.interventions.calibration import calibrate_probability, get_intervention_costs_minor
from app.domain.interventions.erv_calculator import calculate_erv

class InterventionGenerationError(Exception):
    pass

async def generate_and_rank_candidates(session: AsyncSession, case_id: uuid.UUID) -> list[Intervention]:
    """Generates, scores, ranks, and upserts interventions for a given case."""

    # 1. Gates
    case = await session.execute(select(Case).where(Case.id == case_id))
    case = case.scalar_one_or_none()

    if not case:
        raise InterventionGenerationError("Case not found")

    if case.status == CaseStatus.STOPPED:
        return []

    if case.assignment_group != AssignmentGroup.TREATMENT:
        return []

    # 2. Get diagnosis
    diagnosis = await session.execute(select(AIDiagnosis).where(AIDiagnosis.case_id == case_id))
    diagnosis = diagnosis.scalar_one_or_none()

    if not diagnosis:
        raise InterventionGenerationError("Missing AIDiagnosis")

    applicable_types = get_applicable_interventions(diagnosis.diagnosis_category)
    if not applicable_types:
        return []

    # 3. Generate candidates
    candidates_data = []

    recoverable_amount_minor = case.amount_at_risk_minor

    for int_type in applicable_types:
        # Calibration
        calib_input = CalibrationInput(
            intervention_type=int_type,
            diagnosis_category=diagnosis.diagnosis_category,
            ai_recovery_probability=diagnosis.recovery_probability
        )
        final_bps = calibrate_probability(calib_input)

        cost_minor, risk_minor = get_intervention_costs_minor(int_type)

        # ERV math
        erv_params = ERVCalculationParams(
            probability_bps=final_bps,
            recoverable_amount_minor=recoverable_amount_minor,
            intervention_cost_minor=cost_minor,
            risk_penalty_minor=risk_minor
        )
        erv_result = calculate_erv(erv_params)

        candidates_data.append({
            "id": uuid.uuid4(),
            "case_id": case_id,
            "diagnosis_id": diagnosis.id,
            "intervention_type": int_type.value,
            "recoverable_amount_minor": recoverable_amount_minor,
            "currency": case.currency,
            "estimated_recovery_probability_bps": final_bps,
            "intervention_cost_minor": cost_minor,
            "risk_penalty_minor": risk_minor,
            "expected_recovery_value_minor": erv_result.erv_minor,
        })

    # 4. Deterministic Ranking
    # Priority enum ordering for tie breaking
    priority_order = {
        InterventionType.SMART_RETRY: 4,
        InterventionType.PAYMENT_LINK: 3,
        InterventionType.DUNNING_EMAIL: 2,
        InterventionType.MANUAL_REVIEW: 1
    }

    candidates_data.sort(key=lambda c: (
        c["expected_recovery_value_minor"],
        c["estimated_recovery_probability_bps"],
        priority_order.get(InterventionType(c["intervention_type"]), 0),
        c["intervention_type"]
    ), reverse=True)

    for idx, c in enumerate(candidates_data):
        c["rank"] = idx + 1

    # 5. Upsert to DB
    upserted_interventions = []
    for c_data in candidates_data:
        stmt = insert(Intervention).values(**c_data)

        update_dict = {
            "diagnosis_id": stmt.excluded.diagnosis_id,
            "recoverable_amount_minor": stmt.excluded.recoverable_amount_minor,
            "currency": stmt.excluded.currency,
            "estimated_recovery_probability_bps": stmt.excluded.estimated_recovery_probability_bps,
            "intervention_cost_minor": stmt.excluded.intervention_cost_minor,
            "risk_penalty_minor": stmt.excluded.risk_penalty_minor,
            "expected_recovery_value_minor": stmt.excluded.expected_recovery_value_minor,
            "rank": stmt.excluded.rank,
        }

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['case_id', 'intervention_type'],
            set_=update_dict
        ).returning(Intervention)

        result = await session.execute(upsert_stmt)
        upserted_interventions.append(result.scalar_one())

    return upserted_interventions
