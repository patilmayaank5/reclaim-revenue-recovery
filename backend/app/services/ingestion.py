import logging
import uuid
from datetime import timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domain.risk.rules import classify_risk
from app.models.case import Case
from app.models.ingestion_event import IngestionEvent
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.schemas.ingestion import IngestionResponse, NormalizedPaymentEvent

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Base exception for ingestion errors."""
    pass


class DuplicateEventError(IngestionError):
    """Raised when an event has already been processed."""
    pass


class UnknownMerchantError(IngestionError):
    """Raised when the merchant_id does not exist."""
    pass


async def process_payment_event(
    session: AsyncSession, event: NormalizedPaymentEvent
) -> IngestionResponse:
    """Process an incoming normalized payment event transactionally.

    1. Explicit merchant validation.
    2. Enforce idempotency on event_id.
    3. Persist or update the Payment record.
    4. Record the IngestionEvent.
    5. Evaluate risk classification.
    6. Conditionally create a Case.
    """

    try:
        merchant_uuid = uuid.UUID(event.merchant_id)
    except ValueError:
        raise IngestionError(f"Invalid merchant_id format: {event.merchant_id}")

    # 1. Explicit merchant check
    merchant_result = await session.execute(
        select(Merchant).where(Merchant.id == merchant_uuid)
    )
    if not merchant_result.scalar_one_or_none():
        raise UnknownMerchantError(f"Merchant ID {event.merchant_id} not found.")

    # 2. Event Idempotency Check
    event_result = await session.execute(
        select(IngestionEvent).where(IngestionEvent.event_id == event.event_id)
    )
    existing_ingestion_event = event_result.scalar_one_or_none()

    if existing_ingestion_event:
        logger.info(f"Duplicate ingestion event received: {event.event_id}")

        # We need to return existing payment/case IDs
        payment_id_str = str(existing_ingestion_event.payment_id)
        case_result = await session.execute(
            select(Case).where(Case.payment_id == existing_ingestion_event.payment_id)
        )
        existing_case = case_result.scalars().first()

        return IngestionResponse(
            status="idempotent_success",
            payment_id=payment_id_str,
            case_id=str(existing_case.id) if existing_case else None,
            message="Event already processed.",
        )

    # Ensure timestamp is timezone aware
    timestamp = event.event_timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    # 3. Handle Payment identity
    payment_result = await session.execute(
        select(Payment).where(Payment.external_id == event.external_id)
    )
    payment = payment_result.scalar_one_or_none()

    if not payment:
        payment = Payment(
            merchant_id=merchant_uuid,
            external_id=event.external_id,
            amount_minor=event.amount_minor,
            currency=event.currency,
            status=event.status,
            payment_method=event.payment_method,
            failure_code=event.failure_code,
            failure_description=event.failure_description,
            provider=event.provider,
            external_metadata=event.external_metadata,
            attempted_at=timestamp,
        )
        session.add(payment)
    else:
        # Update existing payment with latest event data
        payment.status = event.status
        if event.failure_code:
            payment.failure_code = event.failure_code
        if event.failure_description:
            payment.failure_description = event.failure_description
        payment.external_metadata = event.external_metadata

    # Flush to secure the payment.id if newly created
    try:
        await session.flush()
    except IntegrityError as e:
        await session.rollback()
        raise IngestionError(f"Database constraint error during payment flush: {e}")

    # 4. Record the Ingestion Event
    ingestion_record = IngestionEvent(
        event_id=event.event_id,
        payment_id=payment.id,
        processed_at=timestamp
    )
    session.add(ingestion_record)

    # 5. Evaluate risk classification
    risk_result = classify_risk(event)

    case_id_str = None

    # Check if a case already exists
    case_result = await session.execute(
        select(Case).where(Case.payment_id == payment.id)
    )
    existing_case = case_result.scalars().first()

    if risk_result.is_at_risk:
        if not existing_case:
            # 6. Create a Case
            case = Case(
                merchant_id=merchant_uuid,
                payment_id=payment.id,
                status=risk_result.initial_status,
                amount_at_risk_minor=payment.amount_minor,
                currency=payment.currency,
                failure_category=risk_result.failure_category,
                assignment_group=None,  # Do not assign in Phase 2
                detected_at=timestamp,
            )
            session.add(case)
            await session.flush()
            case_id_str = str(case.id)
        else:
            # Case exists, we just reflect the risk status update if appropriate
            # (In a real system, state machines dictate allowed transitions)
            case_id_str = str(existing_case.id)
            existing_case.status = risk_result.initial_status
            if risk_result.failure_category:
                existing_case.failure_category = risk_result.failure_category
    else:
        if existing_case:
            case_id_str = str(existing_case.id)

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise IngestionError(f"Database constraint error during final commit: {e}")

    return IngestionResponse(
        status="success",
        payment_id=str(payment.id),
        case_id=case_id_str,
    )
