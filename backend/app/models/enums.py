"""Domain enums for Reclaim.

Explicit string enums for lifecycle statuses throughout the recovery pipeline.
Aligned with the frozen Reclaim architecture.
"""

import enum


class PaymentStatus(str, enum.Enum):
    """Payment lifecycle status."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class CaseStatus(str, enum.Enum):
    """Revenue-at-risk case lifecycle status.

    Maps to the 12-step frozen recovery pipeline:
    detected -> enriched -> diagnosed -> intervention_planned
    -> action_pending -> action_approved -> action_executing
    -> action_executed -> verifying -> recovered / not_recovered
    -> closed / stopped
    """

    DETECTED = "detected"
    ENRICHED = "enriched"
    DIAGNOSED = "diagnosed"
    INTERVENTION_PLANNED = "intervention_planned"
    ACTION_PENDING = "action_pending"
    ACTION_APPROVED = "action_approved"
    ACTION_EXECUTING = "action_executing"
    ACTION_EXECUTED = "action_executed"
    VERIFYING = "verifying"
    RECOVERED = "recovered"
    NOT_RECOVERED = "not_recovered"
    CLOSED = "closed"
    STOPPED = "stopped"


class AssignmentGroup(str, enum.Enum):
    """Experiment assignment group.

    Holdout assignment happens deterministically BEFORE AI processing.
    Holdout cases receive no AI processing or intervention.
    """

    TREATMENT = "treatment"
    HOLDOUT = "holdout"


class ActionStatus(str, enum.Enum):
    """Action lifecycle status."""

    PLANNED = "planned"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalStatus(str, enum.Enum):
    """Approval decision status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VerificationStatus(str, enum.Enum):
    """Verification outcome status.

    Verification is a separate domain step.
    HTTP 200 alone is NOT sufficient to declare money recovered.
    """

    PENDING = "pending"
    VERIFIED_RECOVERED = "verified_recovered"
    VERIFIED_NOT_RECOVERED = "verified_not_recovered"
    VERIFICATION_FAILED = "verification_failed"
    INCONCLUSIVE = "inconclusive"


class ExperimentStatus(str, enum.Enum):
    """Experiment lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AuditEventType(str, enum.Enum):
    """Audit event types covering important pipeline operations."""

    CASE_CREATED = "case_created"
    CASE_ENRICHED = "case_enriched"
    DIAGNOSIS_COMPLETED = "diagnosis_completed"
    INTERVENTION_GENERATED = "intervention_generated"
    ACTION_PLANNED = "action_planned"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_DECIDED = "approval_decided"
    ACTION_EXECUTED = "action_executed"
    VERIFICATION_COMPLETED = "verification_completed"
    DEMO_RESET_EXECUTED = "demo_reset_executed"
    EXPERIMENT_ASSIGNED = "experiment_assigned"
    POLICY_EVALUATED = "policy_evaluated"
