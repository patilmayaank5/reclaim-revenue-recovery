import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.domain.providers.razorpay import ProviderConfigurationError
from app.domain.verifications.schemas import (
    VerificationDetailResponse,
    VerificationRequestPayload,
)
from app.services.verification_service import (
    ActionNotVerifiableError,
    VerificationServiceError,
    verify_action,
)

router = APIRouter()


@router.post("/actions/{action_id}/verify", response_model=VerificationDetailResponse)
async def verify_action_endpoint(
    action_id: uuid.UUID,
    payload: VerificationRequestPayload | None = None,
    session: AsyncSession = Depends(get_db),
) -> VerificationDetailResponse:
    """Triggers payment recovery verification for an executed or ambiguous Action."""
    provider_name = payload.provider if payload else None
    verification_scenario = payload.verification_scenario if payload else None
    try:
        return await verify_action(
            session,
            action_id=action_id,
            provider_name=provider_name,
            verification_scenario=verification_scenario,
        )
    except ActionNotVerifiableError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ProviderConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VerificationServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during verification.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected verification error: {str(e)}",
        )
