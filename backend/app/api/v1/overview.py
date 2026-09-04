from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.case import Case
from app.models.payment import Payment
from app.models.approval import Approval
from app.models.action import Action
from app.models.verification import Verification
from app.models.enums import CaseStatus, ApprovalStatus, VerificationStatus, ActionStatus

router = APIRouter()


@router.get("/overview/metrics", summary="Get control room aggregate overview metrics")
async def get_overview_metrics(
    session: AsyncSession = Depends(get_db),
):
    """Returns aggregate operational KPIs for Reclaim Control Room dashboard."""
    # Revenue at Risk (sum of amount_at_risk_minor for active cases)
    risk_stmt = select(func.coalesce(func.sum(Case.amount_at_risk_minor), 0))
    risk_res = await session.execute(risk_stmt)
    revenue_at_risk_minor = risk_res.scalar() or 0

    # Recovered Revenue (sum of recovered_amount_minor from VERIFIED_RECOVERED verifications)
    rec_stmt = select(func.coalesce(func.sum(Verification.recovered_amount_minor), 0)).where(
        Verification.status == VerificationStatus.VERIFIED_RECOVERED
    )
    rec_res = await session.execute(rec_stmt)
    recovered_revenue_minor = rec_res.scalar() or 0

    # Active Cases count
    cases_stmt = select(func.count(Case.id))
    cases_res = await session.execute(cases_stmt)
    total_cases = cases_res.scalar() or 0

    # Pending Approvals count
    appr_stmt = select(func.count(Approval.id)).where(Approval.status == ApprovalStatus.PENDING)
    appr_res = await session.execute(appr_stmt)
    pending_approvals = appr_res.scalar() or 0

    # Pipeline breakdown by CaseStatus
    pipeline_counts = {}
    for st in CaseStatus:
        st_stmt = select(func.count(Case.id)).where(Case.status == st)
        st_res = await session.execute(st_stmt)
        pipeline_counts[st.value] = st_res.scalar() or 0

    # Recovery Rate in BPS (recovered / risk)
    recovery_rate_bps = (
        (recovered_revenue_minor * 10000) // revenue_at_risk_minor
        if revenue_at_risk_minor > 0
        else 0
    )

    return {
        "revenue_at_risk_minor": revenue_at_risk_minor,
        "recovered_revenue_minor": recovered_revenue_minor,
        "recovery_rate_bps": recovery_rate_bps,
        "total_cases": total_cases,
        "pending_approvals": pending_approvals,
        "pipeline_counts": pipeline_counts,
        "currency": "INR",
    }
