import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.providers.base import ExecutionProvider, VerificationRequest, VerificationResponse
from app.domain.providers.razorpay import ProviderConfigurationError, RazorpayProvider
from app.domain.providers.simulator import SimulatorProvider
from app.domain.verifications.schemas import VerificationDetailResponse
from app.models.action import Action
from app.models.audit_event import AuditEvent
from app.models.case import Case
from app.models.enums import (
    ActionStatus,
    AuditEventType,
    CaseStatus,
    PaymentStatus,
    VerificationStatus,
)
from app.models.intervention import Intervention
from app.models.payment import Payment
from app.models.verification import Verification


class VerificationServiceError(Exception):
    """Base exception for verification service errors."""
    pass


class ActionNotVerifiableError(VerificationServiceError):
    """Raised when an action is ineligible for verification."""
    pass


def _resolve_provider(provider_name: str | None) -> ExecutionProvider:
    """Resolves provider instance for verification lookup."""
    target_provider = (provider_name or settings.EXECUTION_DEFAULT_PROVIDER).lower().strip()
    if target_provider == "razorpay":
        return RazorpayProvider()
    return SimulatorProvider()


async def verify_action(
    session: AsyncSession,
    action_id: uuid.UUID,
    provider_name: str | None = None,
    verification_scenario: str | None = None,
) -> VerificationDetailResponse:
    """Verifies payment recovery status for an executed or ambiguous Action."""

    # ============================================================
    # STEP 1: VERIFICATION ELIGIBILITY & IDEMPOTENCY (Short DB Tx)
    # ============================================================
    action_stmt = select(Action).where(Action.id == action_id).with_for_update()
    action_res = await session.execute(action_stmt)
    action = action_res.scalar_one_or_none()

    if not action:
        raise ActionNotVerifiableError(f"Action with ID {action_id} not found")

    is_ambiguous = (action.execution_metadata or {}).get("ambiguous", False)

    # Eligibility check: Action must be EXECUTED or EXECUTING (if ambiguous)
    if action.status == ActionStatus.EXECUTING and not is_ambiguous:
        raise ActionNotVerifiableError("Cannot verify active executing action before completion or timeout")
    elif action.status not in (ActionStatus.EXECUTED, ActionStatus.EXECUTING):
        raise ActionNotVerifiableError(
            f"Cannot verify Action in status '{action.status.value}'. Must be executed or ambiguous executing."
        )

    # Fetch Case
    case_stmt = select(Case).where(Case.id == action.case_id).with_for_update()
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case:
        raise ActionNotVerifiableError(f"Case with ID {action.case_id} not found")

    if case.status == CaseStatus.VERIFYING:
        raise ActionNotVerifiableError("Verification is already in progress for this case")

    if case.status in (CaseStatus.STOPPED, CaseStatus.CLOSED):
        raise ActionNotVerifiableError(f"Cannot verify action for case in status '{case.status.value}'")

    # Fetch Intervention
    interv_stmt = select(Intervention).where(Intervention.id == action.intervention_id)
    interv_res = await session.execute(interv_stmt)
    intervention = interv_res.scalar_one_or_none()

    if not intervention:
        raise ActionNotVerifiableError(f"Intervention with ID {action.intervention_id} not found")

    if intervention.intervention_type == "manual_review":
        raise ActionNotVerifiableError("Intervention 'manual_review' cannot be verified as payment execution")

    # Idempotency check: Return existing canonical terminal verification if already completed
    verif_stmt = select(Verification).where(Verification.action_id == action_id)
    verif_res = await session.execute(verif_stmt)
    existing_verif = verif_res.scalar_one_or_none()

    if existing_verif and existing_verif.status in (
        VerificationStatus.VERIFIED_RECOVERED,
        VerificationStatus.VERIFIED_NOT_RECOVERED,
    ):
        return VerificationDetailResponse.model_validate(existing_verif)

    # Claim verifying state on case
    selected_provider_name = (provider_name or action.provider or settings.EXECUTION_DEFAULT_PROVIDER).lower().strip()
    case.status = CaseStatus.VERIFYING

    request_metadata = dict(action.execution_metadata or {})
    if verification_scenario:
        request_metadata["verification_scenario"] = verification_scenario

    verif_request = VerificationRequest(
        action_id=action.id,
        case_id=action.case_id,
        payment_id=case.payment_id,
        provider=selected_provider_name,
        provider_transaction_id=request_metadata.get("provider_transaction_id"),
        intervention_type=intervention.intervention_type,
        amount_minor=intervention.recoverable_amount_minor,
        currency=intervention.currency,
        metadata=request_metadata,
    )

    # Commit Step 1 transaction to release DB lock before calling provider lookup
    await session.commit()

    # ============================================================
    # STEP 2: PROVIDER LOOKUP (OUTSIDE DB Transaction)
    # Status / evidence lookup only. NEVER calls execution service!
    # ============================================================
    try:
        provider_instance = _resolve_provider(selected_provider_name)
        response: VerificationResponse = await provider_instance.verify(verif_request)
    except Exception as e:
        now_iso = datetime.now(timezone.utc).isoformat()
        response = VerificationResponse(
            status=VerificationStatus.VERIFICATION_FAILED,
            observed_payment_status=None,
            recovered_amount_minor=None,
            currency=intervention.currency,
            provider_event_id=None,
            provider_event_data={"error_class": e.__class__.__name__, "error_detail": str(e)},
            verified_at=now_iso,
        )

    # ============================================================
    # STEP 3: RECORD RESULT & STATUS MUTATIONS (Short DB Tx)
    # ============================================================
    action_stmt_step3 = select(Action).where(Action.id == action_id).with_for_update()
    action_res_step3 = await session.execute(action_stmt_step3)
    action_db = action_res_step3.scalar_one()

    case_stmt_step3 = select(Case).where(Case.id == action_db.case_id).with_for_update()
    case_res_step3 = await session.execute(case_stmt_step3)
    case_db = case_res_step3.scalar_one()

    payment_stmt_step3 = select(Payment).where(Payment.id == case_db.payment_id).with_for_update()
    payment_res_step3 = await session.execute(payment_stmt_step3)
    payment_db = payment_res_step3.scalar_one()

    verif_stmt_step3 = select(Verification).where(Verification.action_id == action_id).with_for_update()
    verif_res_step3 = await session.execute(verif_stmt_step3)
    verif_db = verif_res_step3.scalar_one_or_none()

    # Terminal verification protection: If a terminal verification was recorded by a racing request, preserve it!
    if verif_db and verif_db.status in (
        VerificationStatus.VERIFIED_RECOVERED,
        VerificationStatus.VERIFIED_NOT_RECOVERED,
    ):
        await session.commit()
        return VerificationDetailResponse.model_validate(verif_db)

    now = datetime.now(timezone.utc)

    if not verif_db:
        verif_db = Verification(
            id=uuid.uuid4(),
            action_id=action_db.id,
            case_id=case_db.id,
            payment_id=payment_db.id,
            status=response.status,
            observed_payment_status=response.observed_payment_status,
            recovered_amount_minor=response.recovered_amount_minor,
            currency=response.currency,
            provider_event_id=response.provider_event_id,
            provider_event_data=response.provider_event_data,
            verified_at=now,
        )
        session.add(verif_db)
    else:
        verif_db.status = response.status
        verif_db.observed_payment_status = response.observed_payment_status
        verif_db.recovered_amount_minor = response.recovered_amount_minor
        verif_db.currency = response.currency
        verif_db.provider_event_id = response.provider_event_id
        verif_db.provider_event_data = response.provider_event_data
        verif_db.verified_at = now

    # PAYMENT STATUS MUTATION & ACTION/CASE STATE DISCIPLINE
    if response.status == VerificationStatus.VERIFIED_RECOVERED:
        # ONLY place allowed to transition payment status to CAPTURED
        payment_db.status = PaymentStatus.CAPTURED
        case_db.status = CaseStatus.RECOVERED
        case_db.resolved_at = now
        if action_db.status == ActionStatus.EXECUTING:
            action_db.status = ActionStatus.EXECUTED
            action_db.executed_at = now
            meta = dict(action_db.execution_metadata or {})
            meta["ambiguous"] = False
            meta["requires_verification"] = False
            action_db.execution_metadata = meta

    elif response.status == VerificationStatus.VERIFIED_NOT_RECOVERED:
        # Payment.status strictly UNCHANGED
        case_db.status = CaseStatus.NOT_RECOVERED
        case_db.resolved_at = now
        if action_db.status == ActionStatus.EXECUTING:
            action_db.status = ActionStatus.FAILED
            action_db.executed_at = now
            meta = dict(action_db.execution_metadata or {})
            meta["ambiguous"] = False
            meta["requires_verification"] = False
            action_db.execution_metadata = meta

    elif response.status in (VerificationStatus.PENDING, VerificationStatus.VERIFICATION_FAILED, VerificationStatus.INCONCLUSIVE):
        # Payment.status strictly UNCHANGED
        case_db.status = CaseStatus.VERIFYING
        if action_db.status == ActionStatus.EXECUTING:
            # Retain ambiguous executing state for future verification
            meta = dict(action_db.execution_metadata or {})
            meta["ambiguous"] = True
            meta["requires_verification"] = True
            action_db.execution_metadata = meta

    # Audit event logging
    audit_data = {
        "verification_id": str(verif_db.id),
        "action_id": str(action_db.id),
        "case_id": str(case_db.id),
        "payment_id": str(payment_db.id),
        "verification_status": response.status.value,
        "observed_payment_status": response.observed_payment_status,
        "recovered_amount_minor": response.recovered_amount_minor,
        "provider": selected_provider_name,
        "provider_event_id": response.provider_event_id,
        "verified_at": now.isoformat(),
    }

    session.add(
        AuditEvent(
            id=uuid.uuid4(),
            event_type=AuditEventType.VERIFICATION_COMPLETED,
            entity_type="verification",
            entity_id=verif_db.id,
            actor="verification_service",
            event_data=audit_data,
        )
    )

    await session.commit()
    return VerificationDetailResponse.model_validate(verif_db)
