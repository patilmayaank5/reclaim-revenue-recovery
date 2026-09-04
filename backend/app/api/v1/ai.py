import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.case import Case
from app.services.ai_orchestrator import (
    AIEligibilityError,
    AIOrchestratorError,
    diagnose_case,
)
from app.domain.ai.provider import FakeAIProvider

router = APIRouter()

@router.post(
    "/{case_id}/diagnose",
    status_code=status.HTTP_200_OK,
    summary="Generate AI Diagnosis for Case",
    description="Calls AI provider to generate a structured diagnosis for TREATMENT cases.",
)
async def ai_diagnose(
    case_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    # Optional inject for testing, usually we rely on DI or normal defaults
):
    try:
        # Note: We pass provider=None by default, relying on orchestrator's ClaudeProvider
        # unless running in a specific test context where we inject a provider.
        diagnosis = await diagnose_case(session, case_id)

        return {
            "case_id": str(diagnosis.case_id),
            "diagnosis": diagnosis.diagnosis_category,
            "reason": diagnosis.evidence.get("reason"),
            "ai_confidence": diagnosis.ai_confidence,
            "recovery_probability": diagnosis.recovery_probability,
            "evidence": diagnosis.evidence.get("evidence"),
            "uncertainty": diagnosis.evidence.get("uncertainty"),
            "model": diagnosis.model_name,
            "schema_version": "1.0",
            "created_at": diagnosis.created_at.isoformat() if diagnosis.created_at else None
        }
    except AIEligibilityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIOrchestratorError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during diagnosis."
        )
