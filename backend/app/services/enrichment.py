import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.case import Case
from app.models.case_context import CaseContext
from app.models.merchant import Merchant
from app.models.payment import Payment


async def enrich_case(session: AsyncSession, case: Case) -> CaseContext:
    """Deterministically enrich a Case with structured context.

    Extracts relevant information from the Case, Payment, and Merchant.
    Idempotent: if context exists, it returns it (or updates it).
    """

    # Fetch related Payment and Merchant
    payment_stmt = select(Payment).where(Payment.id == case.payment_id)
    payment_result = await session.execute(payment_stmt)
    payment = payment_result.scalar_one()

    merchant_stmt = select(Merchant).where(Merchant.id == case.merchant_id)
    merchant_result = await session.execute(merchant_stmt)
    merchant = merchant_result.scalar_one()

    # Construct deterministic context
    # Only use basic internal data.
    context_payload = {
        "merchant": {
            "business_type": merchant.business_type,
        },
        "payment": {
            "amount_minor": payment.amount_minor,
            "currency": payment.currency,
            "provider": payment.provider,
            "payment_method": payment.payment_method,
            "failure_code": payment.failure_code,
            "failure_description": payment.failure_description,
        },
        "case": {
            "detected_at": case.detected_at.isoformat(),
            "failure_category": case.failure_category,
        }
    }

    # Check for existing context
    context_stmt = select(CaseContext).where(
        CaseContext.case_id == case.id,
        CaseContext.context_type == "enrichment_baseline"
    )
    context_result = await session.execute(context_stmt)
    existing_context = context_result.scalar_one_or_none()

    if existing_context:
        existing_context.context_data = context_payload
        session.add(existing_context)
        return existing_context
    else:
        new_context = CaseContext(
            case_id=case.id,
            context_type="enrichment_baseline",
            context_data=context_payload,
            source="internal_phase3_enrichment"
        )
        session.add(new_context)
        return new_context
