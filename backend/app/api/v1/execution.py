import uuid
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.domain.actions.schemas import ActionDetailResponse
from app.domain.providers.razorpay import ProviderConfigurationError
from app.services.execution_service import (
    ActionNotExecutableError,
    ExecutionServiceError,
    execute_action,
)

router = APIRouter()


class ExecutionRequestPayload(BaseModel):
    """Optional payload for requesting action execution."""
    provider: str | None = Field(None, description="Optional provider override ('simulator' or 'razorpay')")


@router.post("/actions/{action_id}/execute", response_model=ActionDetailResponse)
async def execute_action_endpoint(
    action_id: uuid.UUID,
    payload: ExecutionRequestPayload | None = None,
    session: AsyncSession = Depends(get_db),
) -> ActionDetailResponse:
    """Triggers execution of an authorized recovery Action."""
    provider_name = payload.provider if payload else None
    try:
        return await execute_action(session, action_id=action_id, provider_name=provider_name)
    except ActionNotExecutableError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ProviderConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ExecutionServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during action execution.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected execution error: {str(e)}",
        )
