import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.domain.actions.schemas import (
    ActionCreateResponse,
    ActionDetailResponse,
    ApprovalDecisionRequest,
)
from app.services.action_service import (
    ActionWorkflowError,
    InvalidApprovalStateError,
    StalePolicyAuthorizationError,
    create_action_for_case,
    decide_approval,
    get_action_details,
)

router = APIRouter()


@router.post("/cases/{case_id}/actions", response_model=ActionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_action(
    case_id: uuid.UUID,
    provider: str = "demo",
    session: AsyncSession = Depends(get_db),
) -> ActionCreateResponse:
    """Evaluates policy authorization and creates an Action / Approval workflow record."""
    try:
        response = await create_action_for_case(session, case_id, provider=provider)
        await session.commit()
        return response
    except StalePolicyAuthorizationError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ActionWorkflowError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during action creation.",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected action workflow error: {str(e)}",
        )


@router.get("/actions/{action_id}", response_model=ActionDetailResponse)
async def get_action(
    action_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ActionDetailResponse:
    """Retrieves Action details and associated human approval status."""
    try:
        return await get_action_details(session, action_id)
    except ActionWorkflowError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error fetching action: {str(e)}",
        )


@router.post("/actions/{action_id}/approve", response_model=ActionDetailResponse)
async def approve_action(
    action_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_db),
) -> ActionDetailResponse:
    """Approves a pending approval action."""
    try:
        response = await decide_approval(
            session,
            action_id=action_id,
            decision="approve",
            approver_id=payload.approver_id,
            decision_reason=payload.decision_reason,
        )
        await session.commit()
        return response
    except InvalidApprovalStateError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ActionWorkflowError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during approval decision.",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected approval decision error: {str(e)}",
        )


@router.post("/actions/{action_id}/reject", response_model=ActionDetailResponse)
async def reject_action(
    action_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_db),
) -> ActionDetailResponse:
    """Rejects a pending approval action."""
    try:
        response = await decide_approval(
            session,
            action_id=action_id,
            decision="reject",
            approver_id=payload.approver_id,
            decision_reason=payload.decision_reason,
        )
        await session.commit()
        return response
    except InvalidApprovalStateError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ActionWorkflowError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during rejection decision.",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected rejection decision error: {str(e)}",
        )


@router.get("/approvals", summary="List actions pending human approval")
async def list_pending_approvals(
    session: AsyncSession = Depends(get_db),
):
    """Returns a list of Action records in PENDING_APPROVAL status."""
    from sqlalchemy import select
    from app.models.action import Action
    from app.models.approval import Approval
    from app.models.case import Case
    from app.models.payment import Payment
    from app.models.intervention import Intervention
    from app.models.enums import ActionStatus, ApprovalStatus

    stmt = select(Approval).where(Approval.status == ApprovalStatus.PENDING).order_by(Approval.requested_at.desc())
    res = await session.execute(stmt)
    approvals = res.scalars().all()

    items = []
    for app in approvals:
        act_res = await session.execute(select(Action).where(Action.id == app.action_id))
        action = act_res.scalar_one_or_none()

        case_res = await session.execute(select(Case).where(Case.id == app.case_id))
        case = case_res.scalar_one_or_none()

        payment = None
        if case:
            pay_res = await session.execute(select(Payment).where(Payment.id == case.payment_id))
            payment = pay_res.scalar_one_or_none()

        intervention = None
        if action:
            inv_res = await session.execute(select(Intervention).where(Intervention.id == action.intervention_id))
            intervention = inv_res.scalar_one_or_none()

        if action and case and payment and intervention:
            items.append({
                "approval_id": str(app.id),
                "action_id": str(action.id),
                "case_id": str(case.id),
                "payment_id": str(payment.id),
                "external_payment_id": payment.external_id,
                "amount_minor": case.amount_at_risk_minor,
                "currency": case.currency,
                "intervention_type": intervention.intervention_type,
                "expected_recovery_value_minor": intervention.expected_recovery_value_minor,
                "estimated_recovery_probability_bps": intervention.estimated_recovery_probability_bps,
                "requested_at": app.requested_at.isoformat() if app.requested_at else None,
                "status": app.status.value,
            })

    return {"items": items, "total": len(items)}
