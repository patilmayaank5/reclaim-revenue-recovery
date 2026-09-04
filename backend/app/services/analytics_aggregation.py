from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.case import Case
from app.models.verification import Verification
from app.models.action import Action
from app.models.intervention import Intervention
from app.models.enums import AssignmentGroup, CaseStatus, VerificationStatus

from app.services.aggregation_schemas import (
    AnalyticsSummary,
    CohortMetrics,
    CohortRecoveryResult,
    InterventionPerformanceRow,
    FailureCategoryRow,
    AnalyticsMetricsResponse
)


async def compute_full_analytics(session: AsyncSession) -> AnalyticsMetricsResponse:
    # 1. Summary
    cases_stmt = select(
        func.count(Case.id),
        func.coalesce(func.sum(Case.amount_at_risk_minor), 0)
    )
    cases_res = await session.execute(cases_stmt)
    total_cases, amount_at_risk = cases_res.one()

    t_cases_stmt = select(func.count(Case.id)).where(Case.assignment_group == AssignmentGroup.TREATMENT)
    t_cases_res = await session.execute(t_cases_stmt)
    treatment_cases = t_cases_res.scalar() or 0

    h_cases_stmt = select(func.count(Case.id)).where(Case.assignment_group == AssignmentGroup.HOLDOUT)
    h_cases_res = await session.execute(h_cases_stmt)
    holdout_cases = h_cases_res.scalar() or 0

    s_cases_stmt = select(func.count(Case.id)).where(Case.status == CaseStatus.STOPPED)
    s_cases_res = await session.execute(s_cases_stmt)
    stopped_cases = s_cases_res.scalar() or 0

    gross_rec_stmt = select(func.coalesce(func.sum(Verification.recovered_amount_minor), 0)).where(
        Verification.status == VerificationStatus.VERIFIED_RECOVERED
    )
    gross_rec_res = await session.execute(gross_rec_stmt)
    gross_recovered = gross_rec_res.scalar() or 0

    gross_rate = (gross_recovered * 10000) // amount_at_risk if amount_at_risk > 0 else 0

    summary = AnalyticsSummary(
        total_cases=total_cases,
        treatment_cases=treatment_cases,
        holdout_cases=holdout_cases,
        stopped_cases=stopped_cases,
        amount_at_risk_minor=amount_at_risk,
        gross_recovered_amount_minor=gross_recovered,
        gross_recovery_rate_bps=gross_rate
    )

    # 2. Cohort Recovery
    # Treatment
    t_risk_stmt = select(func.coalesce(func.sum(Case.amount_at_risk_minor), 0)).where(
        Case.assignment_group == AssignmentGroup.TREATMENT
    )
    t_risk = (await session.execute(t_risk_stmt)).scalar() or 0

    t_rec_stmt = select(
        func.count(func.distinct(Verification.case_id)),
        func.coalesce(func.sum(Verification.recovered_amount_minor), 0)
    ).join(Case, Case.id == Verification.case_id).where(
        and_(
            Verification.status == VerificationStatus.VERIFIED_RECOVERED,
            Case.assignment_group == AssignmentGroup.TREATMENT
        )
    )
    t_rec_res = await session.execute(t_rec_stmt)
    t_rec_count, t_rec_amount = t_rec_res.one()
    t_rate = (t_rec_amount * 10000) // t_risk if t_risk > 0 else 0

    t_metrics = CohortMetrics(
        case_count=treatment_cases,
        amount_at_risk_minor=t_risk,
        recovered_count=t_rec_count,
        recovered_amount_minor=t_rec_amount,
        recovery_rate_bps=t_rate
    )

    # Holdout
    h_risk_stmt = select(func.coalesce(func.sum(Case.amount_at_risk_minor), 0)).where(
        Case.assignment_group == AssignmentGroup.HOLDOUT
    )
    h_risk = (await session.execute(h_risk_stmt)).scalar() or 0

    h_rec_stmt = select(
        func.count(func.distinct(Verification.case_id)),
        func.coalesce(func.sum(Verification.recovered_amount_minor), 0)
    ).join(Case, Case.id == Verification.case_id).where(
        and_(
            Verification.status == VerificationStatus.VERIFIED_RECOVERED,
            Case.assignment_group == AssignmentGroup.HOLDOUT
        )
    )
    h_rec_res = await session.execute(h_rec_stmt)
    h_rec_count, h_rec_amount = h_rec_res.one()
    h_rate = (h_rec_amount * 10000) // h_risk if h_risk > 0 else 0

    h_metrics = CohortMetrics(
        case_count=holdout_cases,
        amount_at_risk_minor=h_risk,
        recovered_count=h_rec_count,
        recovered_amount_minor=h_rec_amount,
        recovery_rate_bps=h_rate
    )

    # Blocker fix: expected metrics
    expected_treatment_recovery_amount = (t_risk * h_rate) // 10000
    incremental_recovery = t_rec_amount - expected_treatment_recovery_amount

    expected_treatment_recovered_cases = (treatment_cases * h_rate) // 10000
    incremental_cases = t_rec_count - expected_treatment_recovered_cases

    cohort_recovery = CohortRecoveryResult(
        treatment=t_metrics,
        holdout=h_metrics,
        incremental_recovered_cases=incremental_cases,
        incremental_recovery_amount_minor=incremental_recovery,
        lift_bps=t_rate - h_rate
    )

    # 3. By Intervention Type (N+1 fix)
    inv_base_stmt = select(
        Intervention.intervention_type,
        func.count(func.distinct(Case.id)),
        func.coalesce(func.sum(Case.amount_at_risk_minor), 0)
    ).join(Action, Action.intervention_id == Intervention.id).join(Case, Case.id == Action.case_id).group_by(Intervention.intervention_type)

    inv_base_res = await session.execute(inv_base_stmt)
    inv_base = inv_base_res.all()

    inv_rec_stmt = select(
        Intervention.intervention_type,
        func.count(func.distinct(Verification.case_id)),
        func.coalesce(func.sum(Verification.recovered_amount_minor), 0)
    ).join(Action, Action.intervention_id == Intervention.id).join(Verification, Verification.action_id == Action.id).where(
        Verification.status == VerificationStatus.VERIFIED_RECOVERED
    ).group_by(Intervention.intervention_type)

    inv_rec_res = await session.execute(inv_rec_stmt)
    inv_rec_map = {row[0]: (row[1], row[2]) for row in inv_rec_res.all()}

    by_intervention = []
    for inv_type, b_cases, b_risk in inv_base:
        r_cases, r_amount = inv_rec_map.get(inv_type, (0, 0))
        rate = (r_amount * 10000) // b_risk if b_risk > 0 else 0
        by_intervention.append(InterventionPerformanceRow(
            intervention_type=inv_type,
            case_count=b_cases,
            recovered_count=r_cases,
            recovered_amount_minor=r_amount,
            recovery_rate_bps=rate
        ))

    # 4. By Failure Category (N+1 fix)
    cat_base_stmt = select(
        Case.failure_category,
        func.count(Case.id),
        func.coalesce(func.sum(Case.amount_at_risk_minor), 0)
    ).where(Case.failure_category.is_not(None)).group_by(Case.failure_category)

    cat_base_res = await session.execute(cat_base_stmt)
    cat_base = cat_base_res.all()

    cat_rec_stmt = select(
        Case.failure_category,
        func.count(func.distinct(Verification.case_id)),
        func.coalesce(func.sum(Verification.recovered_amount_minor), 0)
    ).join(Verification, Verification.case_id == Case.id).where(
        and_(
            Verification.status == VerificationStatus.VERIFIED_RECOVERED,
            Case.failure_category.is_not(None)
        )
    ).group_by(Case.failure_category)

    cat_rec_res = await session.execute(cat_rec_stmt)
    cat_rec_map = {row[0]: (row[1], row[2]) for row in cat_rec_res.all()}

    by_category = []
    for cat, b_cases, b_risk in cat_base:
        r_cases, r_amount = cat_rec_map.get(cat, (0, 0))
        rate = (r_amount * 10000) // b_risk if b_risk > 0 else 0
        by_category.append(FailureCategoryRow(
            failure_category=cat,
            case_count=b_cases,
            amount_at_risk_minor=b_risk,
            recovered_count=r_cases,
            recovered_amount_minor=r_amount,
            recovery_rate_bps=rate
        ))

    # 5. Pipeline Funnel (N+1 fix)
    st_stmt = select(
        Case.status,
        func.count(Case.id)
    ).group_by(Case.status)

    st_res = await session.execute(st_stmt)
    st_map = {row[0]: row[1] for row in st_res.all()}

    pipeline_counts = {}
    for st in CaseStatus:
        pipeline_counts[st.value] = st_map.get(st, 0)

    return AnalyticsMetricsResponse(
        summary=summary,
        cohort_recovery=cohort_recovery,
        by_intervention_type=by_intervention,
        by_failure_category=by_category,
        pipeline_funnel=pipeline_counts
    )
