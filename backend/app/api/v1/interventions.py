import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db
from app.services.intervention_orchestrator import generate_and_rank_candidates, InterventionGenerationError
from pydantic import BaseModel, ConfigDict

router = APIRouter()

class InterventionResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    diagnosis_id: uuid.UUID | None
    intervention_type: str
    recoverable_amount_minor: int
    currency: str
    estimated_recovery_probability_bps: int
    intervention_cost_minor: int
    risk_penalty_minor: int
    expected_recovery_value_minor: int
    rank: int

    model_config = ConfigDict(from_attributes=True)

@router.post("/cases/{case_id}/interventions", response_model=List[InterventionResponse])
async def create_interventions(
    case_id: uuid.UUID,
    session: AsyncSession = Depends(get_db)
):
    try:
        interventions = await generate_and_rank_candidates(session, case_id)
        await session.commit()
        return interventions
    except InterventionGenerationError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database integrity error during candidate upsert."
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
