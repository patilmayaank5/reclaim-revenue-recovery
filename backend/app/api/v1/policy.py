import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.domain.policy.schemas import CasePolicyDecision
from app.services.policy_engine import PolicyEngineError, evaluate_policy_for_case

router = APIRouter()


@router.post("/cases/{case_id}/policy/evaluate", response_model=CasePolicyDecision)
async def evaluate_policy(
    case_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> CasePolicyDecision:
    """Evaluates policy constraints for a revenue-at-risk case and all its intervention candidates."""
    try:
        decision = await evaluate_policy_for_case(session, case_id)
        await session.commit()
        return decision
    except PolicyEngineError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred during policy evaluation.",
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected policy engine error: {str(e)}",
        )
