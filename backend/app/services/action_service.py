import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.domain.actions.schemas import (
    ActionCreateResponse,
    ActionDetailResponse,
    ApprovalResponse,
)
from app.domain.policy.schemas import PolicyOutcome
from app.models.action import Action
from app.models.approval import Approval
from app.models.audit_event import AuditEvent
from app.models.case import Case
from app.models.enums import ActionStatus, ApprovalStatus, AssignmentGroup, AuditEventType, CaseStatus
from app.services.policy_engine import evaluate_policy_for_case


class ActionWorkflowError(Exception):
    """Base exception for action workflow errors."""
    pass


class StalePolicyAuthorizationError(ActionWorkflowError):
    """Raised when authorization context is stale or invalid."""
    pass


class InvalidApprovalStateError(ActionWorkflowError):
    """Raised when approval transition is invalid (e.g. non-pending or already decided)."""
    pass


async def get_action_details(session: AsyncSession, action_id: uuid.UUID) -> ActionDetailResponse:
    """Retrieves an Action and its associated Approval record."""
    action_stmt = select(Action).where(Action.id == action_id)
    action_res = await session.execute(action_stmt)
    action = action_res.scalar_one_or_none()

    if not action:
        raise ActionWorkflowError(f"Action with ID {action_id} not found")

    approval_stmt = select(Approval).where(Approval.action_id == action_id)
    approval_res = await session.execute(approval_stmt)
    approval = approval_res.scalar_one_or_none()

    approval_resp = ApprovalResponse.model_validate(approval) if approval else None

    return ActionDetailResponse(
        id=action.id,
        case_id=action.case_id,
        intervention_id=action.intervention_id,
        status=action.status,
        provider=action.provider,
        idempotency_key=action.idempotency_key,
        execution_metadata=action.execution_metadata,
        scheduled_at=action.scheduled_at,
        executed_at=action.executed_at,
        created_at=action.created_at,
        updated_at=action.updated_at,
        approval=approval_resp,
    )


async def create_action_for_case(
    session: AsyncSession,
    case_id: uuid.UUID,
    provider: str = "demo",
) -> ActionCreateResponse:
    """Evaluates Phase 6 policy and creates an Action / Approval workflow record."""

    # 1. Fetch & Validate Case
    case_stmt = select(Case).where(Case.id == case_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case:
        raise ActionWorkflowError(f"Case with ID {case_id} not found")

    if case.status in (CaseStatus.STOPPED, CaseStatus.CLOSED):
        raise StalePolicyAuthorizationError(f"Cannot create Action for case in status {case.status.value}")

    if case.assignment_group != AssignmentGroup.TREATMENT:
        raise StalePolicyAuthorizationError(f"Case assignment group '{case.assignment_group}' is not eligible for actions")

    # 2. Evaluate Policy
    policy_decision = await evaluate_policy_for_case(session, case_id)

    # 3. Handle BLOCK Outcome
    if policy_decision.overall_outcome == PolicyOutcome.BLOCK:
        return ActionCreateResponse(
            status="blocked",
            overall_outcome=policy_decision.overall_outcome.value,
            selected_reason_code=policy_decision.selected_reason_code.value,
            action=None,
        )

    # 4. Validate Authorized Candidate
    candidate_id = policy_decision.selected_candidate_id
    if not candidate_id:
        raise StalePolicyAuthorizationError("Policy decision permitted action but provided no selected candidate ID")

    idempotency_key = f"action_{case_id}_{candidate_id}"

    # 5. Check for Existing Action (Idempotency)
    existing_action_stmt = select(Action).where(Action.idempotency_key == idempotency_key)
    existing_res = await session.execute(existing_action_stmt)
    existing_action = existing_res.scalar_one_or_none()

    if existing_action:
        # Existing action found. Return idempotently.
        details = await get_action_details(session, existing_action.id)
        return ActionCreateResponse(
            status="existing",
            overall_outcome=policy_decision.overall_outcome.value,
            selected_reason_code=policy_decision.selected_reason_code.value,
            action=details,
        )

    # 6. Map Policy Outcome to Action Status
    if policy_decision.overall_outcome == PolicyOutcome.ALLOW_AUTO:
        action_status = ActionStatus.PLANNED
    elif policy_decision.overall_outcome == PolicyOutcome.REQUIRE_APPROVAL:
        action_status = ActionStatus.PENDING_APPROVAL
    else:
        raise StalePolicyAuthorizationError(f"Unsupported policy outcome: {policy_decision.overall_outcome}")

    # 7. Atomic Action Creation
    new_action_id = uuid.uuid4()

    # Insert Action with Postgres conflict strategy
    insert_action_stmt = (
        insert(Action)
        .values(
            id=new_action_id,
            case_id=case_id,
            intervention_id=candidate_id,
            status=action_status,
            provider=provider,
            idempotency_key=idempotency_key,
            execution_metadata={
                "policy_version": policy_decision.policy_version,
                "reason_code": policy_decision.selected_reason_code.value,
            },
        )
        .on_conflict_do_nothing(index_elements=["idempotency_key"])
        .returning(Action)
    )

    action_res = await session.execute(insert_action_stmt)
    action = action_res.scalar_one_or_none()

    if not action:
        # Race condition handling: Conflict occurred, fetch canonical existing Action
        existing_res = await session.execute(existing_action_stmt)
        existing_action = existing_res.scalar_one()
        details = await get_action_details(session, existing_action.id)
        return ActionCreateResponse(
            status="existing",
            overall_outcome=policy_decision.overall_outcome.value,
            selected_reason_code=policy_decision.selected_reason_code.value,
            action=details,
        )

    # 8. Create Approval if REQUIRE_APPROVAL
    approval_model: Approval | None = None
    if policy_decision.overall_outcome == PolicyOutcome.REQUIRE_APPROVAL:
        approval_model = Approval(
            id=uuid.uuid4(),
            action_id=action.id,
            case_id=case_id,
            status=ApprovalStatus.PENDING,
            requested_at=datetime.now(timezone.utc),
        )
        session.add(approval_model)

    # 9. Update Case Status
    case.status = CaseStatus.ACTION_PENDING

    # 10. Audit Logging
    audit_data_action = {
        "action_id": str(action.id),
        "case_id": str(case_id),
        "intervention_id": str(candidate_id),
        "status": action.status.value,
        "provider": action.provider,
        "idempotency_key": action.idempotency_key,
        "policy_version": policy_decision.policy_version,
        "reason_code": policy_decision.selected_reason_code.value,
    }
    session.add(
        AuditEvent(
            id=uuid.uuid4(),
            event_type=AuditEventType.ACTION_PLANNED,
            entity_type="action",
            entity_id=action.id,
            actor="action_service",
            event_data=audit_data_action,
        )
    )

    if approval_model:
        audit_data_approval = {
            "approval_id": str(approval_model.id),
            "action_id": str(action.id),
            "case_id": str(case_id),
            "status": approval_model.status.value,
            "requested_at": approval_model.requested_at.isoformat(),
        }
        session.add(
            AuditEvent(
                id=uuid.uuid4(),
                event_type=AuditEventType.APPROVAL_REQUESTED,
                entity_type="approval",
                entity_id=approval_model.id,
                actor="action_service",
                event_data=audit_data_approval,
            )
        )

    approval_resp = ApprovalResponse.model_validate(approval_model) if approval_model else None
    details = ActionDetailResponse(
        id=action.id,
        case_id=action.case_id,
        intervention_id=action.intervention_id,
        status=action.status,
        provider=action.provider,
        idempotency_key=action.idempotency_key,
        execution_metadata=action.execution_metadata,
        scheduled_at=action.scheduled_at,
        executed_at=action.executed_at,
        created_at=action.created_at,
        updated_at=action.updated_at,
        approval=approval_resp,
    )

    return ActionCreateResponse(
        status="created",
        overall_outcome=policy_decision.overall_outcome.value,
        selected_reason_code=policy_decision.selected_reason_code.value,
        action=details,
    )


async def decide_approval(
    session: AsyncSession,
    action_id: uuid.UUID,
    decision: str,
    approver_id: str,
    decision_reason: str | None = None,
) -> ActionDetailResponse:
    """Executes a human approval decision (approve or reject) with row-level locking."""
    normalized_decision = decision.lower().strip()
    if normalized_decision not in ("approve", "reject"):
        raise InvalidApprovalStateError(f"Invalid approval decision '{decision}'. Must be 'approve' or 'reject'")

    # Row-level lock on Approval row to prevent concurrency races
    approval_stmt = select(Approval).where(Approval.action_id == action_id).with_for_update()
    approval_res = await session.execute(approval_stmt)
    approval = approval_res.scalar_one_or_none()

    if not approval:
        raise ActionWorkflowError(f"No Approval record found for action ID {action_id}")

    if approval.status != ApprovalStatus.PENDING:
        raise InvalidApprovalStateError(
            f"Cannot decide approval. Approval is in status '{approval.status.value}', expected 'pending'"
        )

    # Row-level lock on Action row
    action_stmt = select(Action).where(Action.id == action_id).with_for_update()
    action_res = await session.execute(action_stmt)
    action = action_res.scalar_one_or_none()

    if not action or action.status != ActionStatus.PENDING_APPROVAL:
        raise InvalidApprovalStateError(
            f"Cannot decide approval. Action status is '{action.status.value if action else 'none'}', expected 'pending_approval'"
        )

    # Fetch Case
    case_stmt = select(Case).where(Case.id == action.case_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case:
        raise ActionWorkflowError(f"Case with ID {action.case_id} not found")

    now = datetime.now(timezone.utc)
    approval.decided_at = now
    approval.approver_id = approver_id
    approval.decision_reason = decision_reason

    if normalized_decision == "approve":
        approval.status = ApprovalStatus.APPROVED
        action.status = ActionStatus.APPROVED
        case.status = CaseStatus.ACTION_APPROVED
    else:
        approval.status = ApprovalStatus.REJECTED
        action.status = ActionStatus.REJECTED
        # Case.status remains ACTION_PENDING or pre-execution state

    # Audit logging
    audit_data = {
        "approval_id": str(approval.id),
        "action_id": str(action.id),
        "case_id": str(action.case_id),
        "decision": normalized_decision,
        "approval_status": approval.status.value,
        "action_status": action.status.value,
        "approver_id": approver_id,
        "decision_reason": decision_reason,
        "decided_at": now.isoformat(),
    }
    session.add(
        AuditEvent(
            id=uuid.uuid4(),
            event_type=AuditEventType.APPROVAL_DECIDED,
            entity_type="approval",
            entity_id=approval.id,
            actor=f"user:{approver_id}",
            event_data=audit_data,
        )
    )

    return await get_action_details(session, action.id)
