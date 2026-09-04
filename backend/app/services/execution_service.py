import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.actions.schemas import ActionDetailResponse
from app.domain.providers.base import (
    ExecutionProvider,
    ExecutionRequest,
    ExecutionResponse,
    ExecutionResultStatus,
)
from app.domain.providers.razorpay import ProviderConfigurationError, RazorpayProvider
from app.domain.providers.simulator import SimulatorProvider
from app.models.action import Action
from app.models.audit_event import AuditEvent
from app.models.case import Case
from app.models.enums import ActionStatus, AssignmentGroup, AuditEventType, CaseStatus
from app.models.intervention import Intervention
from app.services.action_service import get_action_details


class ExecutionServiceError(Exception):
    """Base exception for execution service errors."""
    pass


class ActionNotExecutableError(ExecutionServiceError):
    """Raised when an action is ineligible or invalid for execution."""
    pass


def _resolve_provider(provider_name: str | None) -> ExecutionProvider:
    """Resolves provider instance based on provider name or application settings."""
    target_provider = (provider_name or settings.EXECUTION_DEFAULT_PROVIDER).lower().strip()
    if target_provider == "razorpay":
        return RazorpayProvider()
    return SimulatorProvider()


async def execute_action(
    session: AsyncSession,
    action_id: uuid.UUID,
    provider_name: str | None = None,
) -> ActionDetailResponse:
    """Executes an authorized Action via a 3-step transaction boundary."""

    # ============================================================
    # STEP 1: CLAIM EXECUTION OWNERSHIP (Short DB Transaction)
    # ============================================================
    action_stmt = select(Action).where(Action.id == action_id).with_for_update()
    action_res = await session.execute(action_stmt)
    action = action_res.scalar_one_or_none()

    if not action:
        raise ActionNotExecutableError(f"Action with ID {action_id} not found")

    # Eligibility check
    if action.status not in (ActionStatus.PLANNED, ActionStatus.APPROVED):
        if action.status == ActionStatus.EXECUTING:
            is_ambiguous = (action.execution_metadata or {}).get("ambiguous", False)
            if is_ambiguous:
                raise ActionNotExecutableError(
                    "Cannot re-execute ambiguous action. Ambiguous timeouts require Phase 9 verification."
                )
        raise ActionNotExecutableError(
            f"Cannot execute Action in status '{action.status.value}'. Must be 'planned' or 'approved'."
        )

    # Fetch Case
    case_stmt = select(Case).where(Case.id == action.case_id).with_for_update()
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case:
        raise ActionNotExecutableError(f"Case with ID {action.case_id} not found")

    if case.status in (CaseStatus.STOPPED, CaseStatus.CLOSED):
        raise ActionNotExecutableError(f"Cannot execute action for case in status '{case.status.value}'")

    if case.assignment_group != AssignmentGroup.TREATMENT:
        raise ActionNotExecutableError(f"Case assignment group '{case.assignment_group}' is ineligible for execution")

    # Fetch Intervention
    interv_stmt = select(Intervention).where(Intervention.id == action.intervention_id)
    interv_res = await session.execute(interv_stmt)
    intervention = interv_res.scalar_one_or_none()

    if not intervention:
        raise ActionNotExecutableError(f"Intervention with ID {action.intervention_id} not found")

    if intervention.intervention_type == "manual_review":
        raise ActionNotExecutableError("Intervention 'manual_review' cannot be executed automatically")

    # Claim ownership
    selected_provider_name = (provider_name or action.provider or settings.EXECUTION_DEFAULT_PROVIDER).lower().strip()
    action.status = ActionStatus.EXECUTING
    action.provider = selected_provider_name
    case.status = CaseStatus.ACTION_EXECUTING

    # Prepare execution request payload
    exec_request = ExecutionRequest(
        action_id=action.id,
        case_id=action.case_id,
        payment_id=case.payment_id,
        amount_minor=intervention.recoverable_amount_minor,
        currency=intervention.currency,
        intervention_type=intervention.intervention_type,
        idempotency_key=action.idempotency_key,
        metadata=action.execution_metadata or {},
    )

    # Commit Step 1 transaction to release DB locks before external HTTP call
    await session.commit()

    # ============================================================
    # STEP 2: EXTERNAL PROVIDER EXECUTION (NO DB Transaction)
    # ============================================================
    try:
        provider_instance = _resolve_provider(selected_provider_name)
        response: ExecutionResponse = await provider_instance.execute(exec_request)
    except ProviderConfigurationError:
        raise
    except Exception as e:
        # Fallback for unhandled provider/network exceptions $\rightarrow$ Ambiguous Timeout
        now_iso = datetime.now(timezone.utc).isoformat()
        response = ExecutionResponse(
            status=ExecutionResultStatus.AMBIGUOUS_TIMEOUT,
            provider_transaction_id=None,
            error_code="UNHANDLED_NETWORK_EXCEPTION",
            error_class=e.__class__.__name__,
            requires_verification=True,
            ambiguous=True,
            attempt_timestamp=now_iso,
        )

    # ============================================================
    # STEP 3: RECORD NORMALIZED RESULT (Short DB Transaction)
    # ============================================================
    action_stmt_step3 = select(Action).where(Action.id == action_id).with_for_update()
    action_res_step3 = await session.execute(action_stmt_step3)
    action_db = action_res_step3.scalar_one()

    case_stmt_step3 = select(Case).where(Case.id == action_db.case_id).with_for_update()
    case_res_step3 = await session.execute(case_stmt_step3)
    case_db = case_res_step3.scalar_one()

    now = datetime.now(timezone.utc)
    current_metadata = action_db.execution_metadata or {}

    normalized_metadata: dict[str, Any] = {
        **current_metadata,
        "provider": selected_provider_name,
        "provider_transaction_id": response.provider_transaction_id,
        "execution_outcome": response.status.value,
        "error_code": response.error_code,
        "error_class": response.error_class,
        "requires_verification": response.requires_verification,
        "ambiguous": response.ambiguous,
        "attempt_timestamp": response.attempt_timestamp,
    }

    if response.status == ExecutionResultStatus.SUCCESS:
        action_db.status = ActionStatus.EXECUTED
        action_db.executed_at = now
        case_db.status = CaseStatus.ACTION_EXECUTED
    elif response.status in (ExecutionResultStatus.PERMANENT_FAILURE, ExecutionResultStatus.TRANSIENT_FAILURE):
        action_db.status = ActionStatus.FAILED
        action_db.executed_at = now
        case_db.status = CaseStatus.ACTION_EXECUTED
    elif response.status == ExecutionResultStatus.AMBIGUOUS_TIMEOUT:
        # Retain EXECUTING status for Phase 9 verification handoff
        action_db.status = ActionStatus.EXECUTING
        action_db.executed_at = None

    action_db.execution_metadata = normalized_metadata

    # Audit logging
    audit_data = {
        "action_id": str(action_db.id),
        "case_id": str(action_db.case_id),
        "provider": selected_provider_name,
        "execution_outcome": response.status.value,
        "provider_transaction_id": response.provider_transaction_id,
        "requires_verification": response.requires_verification,
        "ambiguous": response.ambiguous,
        "attempt_timestamp": response.attempt_timestamp,
    }
    session.add(
        AuditEvent(
            id=uuid.uuid4(),
            event_type=AuditEventType.ACTION_EXECUTED,
            entity_type="action",
            entity_id=action_db.id,
            actor="execution_service",
            event_data=audit_data,
        )
    )

    await session.commit()
    return await get_action_details(session, action_db.id)
