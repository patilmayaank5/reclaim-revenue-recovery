import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.case import Case
from app.services.enrichment import enrich_case
from app.services.experiment_assignment import (
    NoActiveExperimentError,
    TerminalCaseError,
    assign_experiment,
)

router = APIRouter()


@router.post(
    "/{case_id}/prepare",
    status_code=status.HTTP_200_OK,
    summary="Prepare Case for Phase 4 (Enrichment + Assignment)",
    description="Deterministically enriches a case context and assigns it to an active experiment (Treatment/Holdout).",
)
async def prepare_case_for_ai(
    case_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    # 1. Load the case
    case_stmt = select(Case).where(Case.id == case_id)
    case_result = await session.execute(case_stmt)
    case = case_result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found."
        )

    try:
        # 2. Enrich context
        context = await enrich_case(session, case)

        # 3 & 4. Select experiment & assign
        assignment = await assign_experiment(session, case)

        # 5. Persist results
        await session.commit()

    except TerminalCaseError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NoActiveExperimentError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment conflict due to concurrent requests."
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during preparation."
        )

    # 6. Return Phase 4 contract
    return {
        "case_id": str(case.id),
        "assignment_group": assignment.group.value,
        "experiment_id": str(assignment.experiment_id),
        "enriched_context": context.context_data
    }


@router.get("", summary="List all recovery cases")
async def list_cases(
    status: str | None = None,
    assignment_group: str | None = None,
    search: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    """Returns a list of recovery cases with payment and action state summary."""
    from app.models.payment import Payment
    from app.models.ai_diagnosis import AIDiagnosis
    from app.models.action import Action
    from app.models.verification import Verification

    stmt = select(Case).order_by(Case.created_at.desc())
    if status:
        stmt = stmt.where(Case.status == status)
    if assignment_group:
        stmt = stmt.where(Case.assignment_group == assignment_group)

    result = await session.execute(stmt)
    cases = result.scalars().all()

    items = []
    for c in cases:
        # Load related models safely
        pay_res = await session.execute(select(Payment).where(Payment.id == c.payment_id))
        payment = pay_res.scalar_one_or_none()

        diag_res = await session.execute(select(AIDiagnosis).where(AIDiagnosis.case_id == c.id))
        diagnosis = diag_res.scalar_one_or_none()

        act_res = await session.execute(select(Action).where(Action.case_id == c.id))
        action = act_res.scalar_one_or_none()

        verif_res = await session.execute(select(Verification).where(Verification.case_id == c.id))
        verification = verif_res.scalar_one_or_none()

        if search:
            search_str = search.lower()
            match = (
                search_str in str(c.id).lower()
                or (payment and search_str in payment.external_id.lower())
                or (c.failure_category and search_str in c.failure_category.lower())
            )
            if not match:
                continue

        items.append({
            "id": str(c.id),
            "payment_id": str(c.payment_id),
            "merchant_id": str(c.merchant_id),
            "status": c.status.value,
            "assignment_group": c.assignment_group.value if c.assignment_group else None,
            "amount_at_risk_minor": c.amount_at_risk_minor,
            "currency": c.currency,
            "failure_category": c.failure_category,
            "detected_at": c.detected_at.isoformat() if c.detected_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            "payment": {
                "external_id": payment.external_id,
                "status": payment.status.value,
                "payment_method": payment.payment_method,
                "provider": payment.provider,
                "failure_code": payment.failure_code,
                "failure_description": payment.failure_description,
            } if payment else None,
            "diagnosis": {
                "category": diagnosis.diagnosis_category,
                "ai_confidence": diagnosis.ai_confidence,
                "recovery_probability": diagnosis.recovery_probability,
            } if diagnosis else None,
            "action": {
                "id": str(action.id),
                "status": action.status.value,
                "provider": action.provider,
                "idempotency_key": action.idempotency_key,
                "executed_at": action.executed_at.isoformat() if action.executed_at else None,
                "execution_metadata": action.execution_metadata,
            } if action else None,
            "verification": {
                "status": verification.status.value,
                "observed_payment_status": verification.observed_payment_status,
                "recovered_amount_minor": verification.recovered_amount_minor,
                "verified_at": verification.verified_at.isoformat() if verification.verified_at else None,
            } if verification else None,
        })

    return {"items": items, "total": len(items)}


@router.get("/{case_id}/investigation", summary="Get complete case investigation detail")
async def get_case_investigation(
    case_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    """Returns 6-section investigation data for a case."""
    from app.models.payment import Payment
    from app.models.ai_diagnosis import AIDiagnosis
    from app.models.intervention import Intervention
    from app.models.action import Action
    from app.models.approval import Approval
    from app.models.verification import Verification

    case_stmt = select(Case).where(Case.id == case_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")

    pay_res = await session.execute(select(Payment).where(Payment.id == case.payment_id))
    payment = pay_res.scalar_one_or_none()

    diag_res = await session.execute(select(AIDiagnosis).where(AIDiagnosis.case_id == case.id))
    diagnosis = diag_res.scalar_one_or_none()

    interv_stmt = select(Intervention).where(Intervention.case_id == case.id).order_by(Intervention.rank.asc())
    interv_res = await session.execute(interv_stmt)
    interventions = interv_res.scalars().all()

    act_res = await session.execute(select(Action).where(Action.case_id == case.id))
    action = act_res.scalar_one_or_none()

    approval = None
    if action:
        appr_res = await session.execute(select(Approval).where(Approval.action_id == action.id))
        approval = appr_res.scalar_one_or_none()

    verif_res = await session.execute(select(Verification).where(Verification.case_id == case.id))
    verification = verif_res.scalar_one_or_none()

    return {
        "case": {
            "id": str(case.id),
            "status": case.status.value,
            "assignment_group": case.assignment_group.value if case.assignment_group else None,
            "amount_at_risk_minor": case.amount_at_risk_minor,
            "currency": case.currency,
            "failure_category": case.failure_category,
            "detected_at": case.detected_at.isoformat() if case.detected_at else None,
            "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        },
        "payment": {
            "id": str(payment.id),
            "external_id": payment.external_id,
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "status": payment.status.value,
            "payment_method": payment.payment_method,
            "failure_code": payment.failure_code,
            "failure_description": payment.failure_description,
            "provider": payment.provider,
            "attempted_at": payment.attempted_at.isoformat() if payment.attempted_at else None,
        } if payment else None,
        "diagnosis": {
            "id": str(diagnosis.id),
            "diagnosis_category": diagnosis.diagnosis_category,
            "evidence": diagnosis.evidence,
            "ai_confidence": diagnosis.ai_confidence,
            "recovery_probability": diagnosis.recovery_probability,
            "model_provider": diagnosis.model_provider,
            "model_name": diagnosis.model_name,
        } if diagnosis else None,
        "interventions": [
            {
                "id": str(inv.id),
                "intervention_type": inv.intervention_type,
                "recoverable_amount_minor": inv.recoverable_amount_minor,
                "currency": inv.currency,
                "estimated_recovery_probability_bps": inv.estimated_recovery_probability_bps,
                "intervention_cost_minor": inv.intervention_cost_minor,
                "risk_penalty_minor": inv.risk_penalty_minor,
                "expected_recovery_value_minor": inv.expected_recovery_value_minor,
                "rank": inv.rank,
                "rationale": inv.rationale,
            }
            for inv in interventions
        ],
        "action": {
            "id": str(action.id),
            "intervention_id": str(action.intervention_id),
            "status": action.status.value,
            "provider": action.provider,
            "idempotency_key": action.idempotency_key,
            "execution_metadata": action.execution_metadata,
            "executed_at": action.executed_at.isoformat() if action.executed_at else None,
            "approval": {
                "id": str(approval.id),
                "status": approval.status.value,
                "requested_at": approval.requested_at.isoformat() if approval.requested_at else None,
                "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
                "approver_id": approval.approver_id,
                "decision_reason": approval.decision_reason,
            } if approval else None,
        } if action else None,
        "verification": {
            "id": str(verification.id),
            "status": verification.status.value,
            "observed_payment_status": verification.observed_payment_status,
            "recovered_amount_minor": verification.recovered_amount_minor,
            "currency": verification.currency,
            "provider_event_id": verification.provider_event_id,
            "verified_at": verification.verified_at.isoformat() if verification.verified_at else None,
        } if verification else None,
    }
