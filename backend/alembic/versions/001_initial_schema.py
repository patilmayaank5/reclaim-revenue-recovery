"""Initial schema for Reclaim revenue recovery engine.

Revision ID: 001
Revises: None
Create Date: 2026-09-03

Creates all 12 domain tables:
- merchants
- payments
- cases
- case_contexts
- ai_diagnoses
- interventions
- actions
- approvals
- verifications
- experiments
- experiment_assignments
- audit_events
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- merchants ---
    op.create_table(
        "merchants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("business_type", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_merchants_external_id", "merchants", ["external_id"])

    # --- payments ---
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False, unique=True),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False, comment="Payment amount in integer minor units"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("failure_code", sa.String(100), nullable=True),
        sa.Column("failure_description", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("external_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_payments_merchant_id", "payments", ["merchant_id"])
    op.create_index("ix_payments_external_id", "payments", ["external_id"])
    op.create_index("ix_payments_status", "payments", ["status"])

    # --- cases ---
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("amount_at_risk_minor", sa.BigInteger(), nullable=False, comment="Amount at risk in integer minor units"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("failure_category", sa.String(100), nullable=True),
        sa.Column("assignment_group", sa.String(50), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cases_merchant_id", "cases", ["merchant_id"])
    op.create_index("ix_cases_payment_id", "cases", ["payment_id"])
    op.create_index("ix_cases_status", "cases", ["status"])
    op.create_index("ix_cases_assignment_group", "cases", ["assignment_group"])

    # --- case_contexts ---
    op.create_table(
        "case_contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("context_type", sa.String(100), nullable=False),
        sa.Column("context_data", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_case_contexts_case_id", "case_contexts", ["case_id"])

    # --- ai_diagnoses ---
    op.create_table(
        "ai_diagnoses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("diagnosis_category", sa.String(100), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("ai_confidence", sa.Float(), nullable=False, comment="Raw AI confidence (0-1). NOT recovery probability."),
        sa.Column("recovery_probability", sa.Float(), nullable=True, comment="Calibrated probability, separate from ai_confidence."),
        sa.Column("model_provider", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("raw_response_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_diagnoses_case_id", "ai_diagnoses", ["case_id"])

    # --- interventions ---
    op.create_table(
        "interventions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("diagnosis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_diagnoses.id"), nullable=True),
        sa.Column("intervention_type", sa.String(100), nullable=False),
        sa.Column("recoverable_amount_minor", sa.BigInteger(), nullable=False, comment="Recoverable amount in integer minor units"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("estimated_recovery_probability", sa.Float(), nullable=False),
        sa.Column("intervention_cost_minor", sa.BigInteger(), nullable=False, comment="Intervention cost in integer minor units"),
        sa.Column("risk_penalty_minor", sa.BigInteger(), nullable=False, comment="Risk penalty in integer minor units"),
        sa.Column("expected_recovery_value_minor", sa.BigInteger(), nullable=False, comment="Deterministic ERV in integer minor units"),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interventions_case_id", "interventions", ["case_id"])

    # --- actions ---
    op.create_table(
        "actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("intervention_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interventions.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True, comment="UNIQUE at database level"),
        sa.Column("execution_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_actions_case_id", "actions", ["case_id"])
    op.create_index("ix_actions_status", "actions", ["status"])
    op.create_index("ix_actions_idempotency_key", "actions", ["idempotency_key"])

    # --- approvals ---
    op.create_table(
        "approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actions.id"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approver_id", sa.String(255), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_approvals_action_id", "approvals", ["action_id"])
    op.create_index("ix_approvals_case_id", "approvals", ["case_id"])
    op.create_index("ix_approvals_status", "approvals", ["status"])

    # --- verifications ---
    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actions.id"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("observed_payment_status", sa.String(50), nullable=True),
        sa.Column("recovered_amount_minor", sa.BigInteger(), nullable=True, comment="Verified recovered amount in integer minor units"),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("provider_event_id", sa.String(255), nullable=True),
        sa.Column("provider_event_data", postgresql.JSONB(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_verifications_action_id", "verifications", ["action_id"])
    op.create_index("ix_verifications_case_id", "verifications", ["case_id"])
    op.create_index("ix_verifications_status", "verifications", ["status"])

    # --- experiments ---
    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("segment_filter", postgresql.JSONB(), nullable=True),
        sa.Column("intervention_strategy", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("holdout_percentage", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_experiments_status", "experiments", ["status"])

    # --- experiment_assignments ---
    op.create_table(
        "experiment_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("group", sa.String(50), nullable=False),
        sa.Column("assignment_hash", sa.String(255), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("experiment_id", "case_id", name="uq_experiment_assignment_experiment_case"),
    )
    op.create_index("ix_experiment_assignments_experiment_id", "experiment_assignments", ["experiment_id"])
    op.create_index("ix_experiment_assignments_case_id", "experiment_assignments", ["case_id"])
    op.create_index("ix_experiment_assignments_group", "experiment_assignments", ["group"])

    # --- audit_events ---
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_correlation_id", "audit_events", ["correlation_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("experiment_assignments")
    op.drop_table("experiments")
    op.drop_table("verifications")
    op.drop_table("approvals")
    op.drop_table("actions")
    op.drop_table("interventions")
    op.drop_table("ai_diagnoses")
    op.drop_table("case_contexts")
    op.drop_table("cases")
    op.drop_table("payments")
    op.drop_table("merchants")
