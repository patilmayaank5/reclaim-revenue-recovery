import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ActionStatus, ApprovalStatus


class ApprovalResponse(BaseModel):
    """Schema for human approval record details."""
    id: uuid.UUID
    action_id: uuid.UUID
    case_id: uuid.UUID
    status: ApprovalStatus
    requested_at: datetime | None = None
    decided_at: datetime | None = None
    approver_id: str | None = None
    decision_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ActionDetailResponse(BaseModel):
    """Full details of an Action including nested Approval status."""
    id: uuid.UUID
    case_id: uuid.UUID
    intervention_id: uuid.UUID
    status: ActionStatus
    provider: str
    idempotency_key: str
    execution_metadata: dict | None = None
    scheduled_at: datetime | None = None
    executed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    approval: ApprovalResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ActionCreateResponse(BaseModel):
    """Response payload detailing created or existing Action from policy decision."""
    status: str = Field(description="'created', 'existing', or 'blocked'")
    overall_outcome: str
    selected_reason_code: str
    action: ActionDetailResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalDecisionRequest(BaseModel):
    """Payload for approving or rejecting a pending action."""
    approver_id: str = Field(..., min_length=1, description="ID or username of human approver")
    decision_reason: str | None = Field(None, description="Optional explanation for the decision")
