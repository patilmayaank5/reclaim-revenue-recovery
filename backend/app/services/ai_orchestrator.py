import logging
import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.domain.ai.claude_provider import ClaudeProvider
from app.domain.ai.provider import (
    AINonRetryableError,
    AIProvider,
    AITransientError,
    FakeAIProvider,
)
from app.models.ai_diagnosis import AIDiagnosis
from app.models.case import Case
from app.models.case_context import CaseContext
from app.models.enums import AssignmentGroup, CaseStatus

logger = logging.getLogger(__name__)


class AIOrchestratorError(Exception):
    pass


class AIEligibilityError(AIOrchestratorError):
    pass


async def diagnose_case(
    session: AsyncSession,
    case_id: uuid.UUID,
    provider: Optional[AIProvider] = None
) -> AIDiagnosis:
    """Orchestrates AI diagnosis for a case.

    1. Loads Case and validates TREATMENT gate.
    2. Builds sanitized allowlisted context.
    3. Calls AI provider outside the DB transaction.
    4. Validates provider response.
    5. Starts a short DB transaction to persist.
    """

    # --- 1. Load case and validate TREATMENT gate (Short Read) ---
    stmt = select(Case).where(Case.id == case_id)
    result = await session.execute(stmt)
    case = result.scalar_one_or_none()

    if not case:
        raise AIEligibilityError(f"Case {case_id} not found.")

    if case.status == CaseStatus.STOPPED:
        raise AIEligibilityError("Case is STOPPED. AI diagnosis forbidden.")

    if case.assignment_group != AssignmentGroup.TREATMENT:
        raise AIEligibilityError("Case is not in TREATMENT group. AI diagnosis forbidden.")

    # Check if diagnosis already exists
    diag_stmt = select(AIDiagnosis).where(AIDiagnosis.case_id == case_id)
    diag_result = await session.execute(diag_stmt)
    existing_diagnosis = diag_result.scalar_one_or_none()

    if existing_diagnosis:
        print("DIAGNOSIS ALREADY EXISTS. EXISTING DIAGNOSIS IS:", existing_diagnosis)
        logger.info(f"Diagnosis already exists for case {case_id}")
        return existing_diagnosis

    print("NO EXISTING DIAGNOSIS FOUND. PROCEEDING.")

    # --- 2. Build sanitized allowlisted context ---
    ctx_stmt = select(CaseContext).where(
        CaseContext.case_id == case_id,
        CaseContext.context_type == "enrichment_baseline"
    )
    ctx_result = await session.execute(ctx_stmt)
    case_context = ctx_result.scalar_one_or_none()

    context_data = case_context.context_data if case_context else {}

    # Strict allowlist of input fields
    ai_input = {
        "amount_at_risk_minor": case.amount_at_risk_minor,
        "currency": case.currency,
        "failure_category": case.failure_category,
        "failure_code": context_data.get("payment", {}).get("failure_code"),
        "failure_description": context_data.get("payment", {}).get("failure_description"),
        "merchant_business_type": context_data.get("merchant", {}).get("business_type"),
    }

    # Clean up None values
    ai_input = {k: v for k, v in ai_input.items() if v is not None}

    # We close/release this session scope logically here before doing the slow AI call.
    # In SQLAlchemy async, we just await the network call. We aren't locking rows.

    # --- 3 & 4. Call AI provider & Validate ---
    if not provider:
        # Default to real provider in production, or Fake if not configured?
        # Actually, let's always use ClaudeProvider by default unless injected.
        provider = ClaudeProvider()

    # Retry loop (Max 2 attempts)
    max_attempts = 2
    ai_output = None

    for attempt in range(1, max_attempts + 1):
        try:
            ai_output = await provider.diagnose(ai_input)
            break
        except AITransientError as e:
            logger.warning(f"Transient AI error on attempt {attempt}: {e}")
            if attempt == max_attempts:
                raise AIOrchestratorError("AI diagnosis failed after max transient retries.")
            # We would optionally sleep here
        except AINonRetryableError as e:
            logger.error(f"Non-retryable AI error: {e}")
            raise AIOrchestratorError(f"AI diagnosis failed permanently: {e}")

    if not ai_output:
        raise AIOrchestratorError("Failed to produce AI output.")

    # --- 5. Short DB transaction to persist ---
    provider_name = "anthropic" if isinstance(provider, ClaudeProvider) else "fake"

    new_diagnosis = AIDiagnosis(
        case_id=case_id,
        diagnosis_category=ai_output.diagnosis_category.value,
        evidence={
            "reason": ai_output.reason,
            "evidence": ai_output.evidence,
            "uncertainty": ai_output.uncertainty
        },
        ai_confidence=ai_output.ai_confidence,
        recovery_probability=ai_output.recovery_probability,
        model_provider=provider_name,
        model_name=settings.AI_MODEL,
    )

    session.add(new_diagnosis)

    try:
        await session.commit()
    except IntegrityError:
        # 8. Handle concurrent uniqueness races safely
        await session.rollback()
        # Fetch the one that beat us to it
        concurrent_diag = await session.execute(
            select(AIDiagnosis).where(AIDiagnosis.case_id == case_id)
        )
        return concurrent_diag.scalar_one()

    return new_diagnosis
