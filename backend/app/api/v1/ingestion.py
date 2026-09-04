from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.ingestion import IngestionResponse, NormalizedPaymentEvent
from app.services.ingestion import (
    DuplicateEventError,
    IngestionError,
    UnknownMerchantError,
    process_payment_event,
)

router = APIRouter()


@router.post(
    "/payment-events",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest normalized payment event",
    description="Idempotent endpoint to ingest a normalized provider payment event, creating a Payment and conditionally a Case.",
)
async def ingest_payment_event(
    event: NormalizedPaymentEvent,
    session: AsyncSession = Depends(get_db),
):
    try:
        response = await process_payment_event(session, event)
        return response
    except UnknownMerchantError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IngestionError as e:
        # Generic ingestion error (e.g., db constraint)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Broad catch to return 500 cleanly without leaking traces in response directly
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during ingestion",
        )
