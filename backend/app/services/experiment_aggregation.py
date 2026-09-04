import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.experiment import Experiment
from app.models.experiment_assignment import ExperimentAssignment
from app.models.case import Case
from app.models.verification import Verification
from app.models.action import Action
from app.models.intervention import Intervention
from app.models.payment import Payment
from app.models.enums import AssignmentGroup, CaseStatus, VerificationStatus, PaymentStatus

from app.services.aggregation_schemas import (
    ExperimentSummaryRow,
    ExperimentDetailResult,
    CohortMetrics,
    IncrementalMetrics,
    InterventionBreakdownItem
)


async def compute_experiment_list(session: AsyncSession, status_filter: Optional[str] = None) -> list[ExperimentSummaryRow]:
    stmt = select(Experiment).order_by(Experiment.created_at.desc())
    if status_filter:
        stmt = stmt.where(Experiment.status == status_filter)

    res = await session.execute(stmt)
    experiments = res.scalars().all()

    if not experiments:
        return []

    exp_ids = [e.id for e in experiments]

    # N+1 fix: bulk fetch counts
    counts_stmt = select(
        ExperimentAssignment.experiment_id,
        ExperimentAssignment.group,
        func.count(ExperimentAssignment.case_id)
    ).where(
        ExperimentAssignment.experiment_id.in_(exp_ids)
    ).group_by(
        ExperimentAssignment.experiment_id,
        ExperimentAssignment.group
    )

    counts_res = await session.execute(counts_stmt)
    counts = counts_res.all()

    t_counts = {}
    h_counts = {}
    for eid, grp, cnt in counts:
        if grp == AssignmentGroup.TREATMENT:
            t_counts[eid] = cnt
        elif grp == AssignmentGroup.HOLDOUT:
            h_counts[eid] = cnt

    results = []
    for exp in experiments:
        t_count = t_counts.get(exp.id, 0)
        h_count = h_counts.get(exp.id, 0)

        results.append(ExperimentSummaryRow(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            status=exp.status.value,
            intervention_strategy=exp.intervention_strategy,
            holdout_percentage=exp.holdout_percentage,
            segment_filter=exp.segment_filter,
            started_at=exp.started_at,
            completed_at=exp.completed_at,
            created_at=exp.created_at,
            treatment_count=t_count,
            holdout_count=h_count,
            total_assignments=t_count + h_count
        ))

    return results


async def _compute_cohort_metrics(session: AsyncSession, experiment_id: uuid.UUID, group: AssignmentGroup) -> CohortMetrics:
    cohort_cases_stmt = select(ExperimentAssignment.case_id).where(
        and_(
            ExperimentAssignment.experiment_id == experiment_id,
            ExperimentAssignment.group == group
        )
    )

    base_stmt = select(
        func.count(Case.id),
        func.coalesce(func.sum(Case.amount_at_risk_minor), 0)
    ).where(Case.id.in_(cohort_cases_stmt))

    base_res = await session.execute(base_stmt)
    case_count, amount_at_risk = base_res.one()

    if group == AssignmentGroup.TREATMENT:
        rec_stmt = select(
            func.count(func.distinct(Verification.case_id)),
            func.coalesce(func.sum(Verification.recovered_amount_minor), 0)
        ).where(
            and_(
                Verification.status == VerificationStatus.VERIFIED_RECOVERED,
                Verification.case_id.in_(cohort_cases_stmt)
            )
        )
    else:
        # Holdout recovery is purely Payment CAPTURED and NO Reclaim Action exists
        # Double counting prevention: NOT EXISTS action for this case
        no_action_stmt = select(1).where(Action.case_id == Case.id)

        rec_stmt = select(
            func.count(func.distinct(Case.id)),
            func.coalesce(func.sum(Payment.amount_minor), 0)
        ).select_from(Case).join(
            Payment, Case.payment_id == Payment.id
        ).where(
            and_(
                Case.id.in_(cohort_cases_stmt),
                Payment.status == PaymentStatus.CAPTURED,
                ~no_action_stmt.exists()
            )
        )

    rec_res = await session.execute(rec_stmt)
    recovered_count, recovered_amount = rec_res.one()

    recovery_rate = (recovered_amount * 10000) // amount_at_risk if amount_at_risk > 0 else 0

    return CohortMetrics(
        case_count=case_count,
        amount_at_risk_minor=amount_at_risk,
        recovered_count=recovered_count,
        recovered_amount_minor=recovered_amount,
        recovery_rate_bps=recovery_rate
    )


async def compute_experiment_detail(session: AsyncSession, experiment_id: uuid.UUID) -> Optional[ExperimentDetailResult]:
    exp_stmt = select(Experiment).where(Experiment.id == experiment_id)
    exp_res = await session.execute(exp_stmt)
    exp = exp_res.scalar_one_or_none()

    if not exp:
        return None

    treatment_metrics = await _compute_cohort_metrics(session, experiment_id, AssignmentGroup.TREATMENT)
    holdout_metrics = await _compute_cohort_metrics(session, experiment_id, AssignmentGroup.HOLDOUT)

    # Blocker fix: expected metrics
    expected_treatment_recovery_amount = (treatment_metrics.amount_at_risk_minor * holdout_metrics.recovery_rate_bps) // 10000
    incremental_recovery = treatment_metrics.recovered_amount_minor - expected_treatment_recovery_amount

    expected_treatment_recovered_cases = (treatment_metrics.case_count * holdout_metrics.recovery_rate_bps) // 10000
    incremental_cases = treatment_metrics.recovered_count - expected_treatment_recovered_cases

    lift = treatment_metrics.recovery_rate_bps - holdout_metrics.recovery_rate_bps

    incremental_metrics = IncrementalMetrics(
        incremental_recovered_cases=incremental_cases,
        incremental_recovery_amount_minor=incremental_recovery,
        treatment_recovery_rate_bps=treatment_metrics.recovery_rate_bps,
        holdout_recovery_rate_bps=holdout_metrics.recovery_rate_bps,
        lift_bps=lift
    )

    # N+1 fix: Intervention breakdown
    treatment_cases_stmt = select(ExperimentAssignment.case_id).where(
        and_(
            ExperimentAssignment.experiment_id == experiment_id,
            ExperimentAssignment.group == AssignmentGroup.TREATMENT
        )
    )

    base_breakdown_stmt = select(
        Intervention.intervention_type,
        func.count(func.distinct(Case.id)),
        func.coalesce(func.sum(Case.amount_at_risk_minor), 0)
    ).join(Action, Action.intervention_id == Intervention.id).join(Case, Case.id == Action.case_id).where(
        Action.case_id.in_(treatment_cases_stmt)
    ).group_by(Intervention.intervention_type)

    base_bd_res = await session.execute(base_breakdown_stmt)
    base_bd = base_bd_res.all()

    rec_breakdown_stmt = select(
        Intervention.intervention_type,
        func.count(func.distinct(Verification.case_id)),
        func.coalesce(func.sum(Verification.recovered_amount_minor), 0)
    ).join(Action, Action.intervention_id == Intervention.id).join(Verification, Verification.action_id == Action.id).where(
        and_(
            Verification.status == VerificationStatus.VERIFIED_RECOVERED,
            Verification.case_id.in_(treatment_cases_stmt)
        )
    ).group_by(Intervention.intervention_type)

    rec_bd_res = await session.execute(rec_breakdown_stmt)
    rec_bd = {row[0]: (row[1], row[2]) for row in rec_bd_res.all()}

    breakdown = []
    for inv_type, b_cases, b_risk in base_bd:
        r_cases, r_amount = rec_bd.get(inv_type, (0, 0))
        rate = (r_amount * 10000) // b_risk if b_risk > 0 else 0

        breakdown.append(InterventionBreakdownItem(
            intervention_type=inv_type,
            case_count=b_cases,
            recovered_count=r_cases,
            recovered_amount_minor=r_amount,
            recovery_rate_bps=rate
        ))

    return ExperimentDetailResult(
        experiment=ExperimentSummaryRow(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            status=exp.status.value,
            intervention_strategy=exp.intervention_strategy,
            holdout_percentage=exp.holdout_percentage,
            segment_filter=exp.segment_filter,
            started_at=exp.started_at,
            completed_at=exp.completed_at,
            created_at=exp.created_at,
            treatment_count=treatment_metrics.case_count,
            holdout_count=holdout_metrics.case_count,
            total_assignments=treatment_metrics.case_count + holdout_metrics.case_count
        ),
        cohort_metrics={
            "treatment": treatment_metrics,
            "holdout": holdout_metrics
        },
        incremental_metrics=incremental_metrics,
        intervention_breakdown=breakdown
    )
