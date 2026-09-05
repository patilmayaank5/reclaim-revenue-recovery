"""Phase 1 tests — SQLAlchemy model schema verification.

These tests verify critical architecture guarantees WITHOUT requiring
a running PostgreSQL database. They inspect SQLAlchemy model metadata.

Tests cover:
1. All models importable
2. Monetary columns use BigInteger (not Float)
3. actions.idempotency_key has DB-level UNIQUE constraint
4. Required foreign keys exist
5. AuditEvent has no updated_at column
6. AuditEvent update/delete is blocked by ORM event listeners
7. Enum values are correct
8. ExperimentAssignment supports treatment/holdout
9. ExperimentAssignment has unique constraint on (experiment_id, case_id)
10. AI confidence and recovery probability are separate columns
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import BigInteger, Float, Integer, inspect

# ============================================================
# 1. All models importable
# ============================================================


def test_all_models_importable():
    """All 12 models and all enums can be imported."""
    from app.models import (
        Action,
        AIDiagnosis,
        Approval,
        AuditEvent,
        Case,
        CaseContext,
        Experiment,
        ExperimentAssignment,
        Intervention,
        Merchant,
        Payment,
        Verification,
    )

    models = [
        Action, AIDiagnosis, Approval, AuditEvent, Case, CaseContext,
        Experiment, ExperimentAssignment, Intervention, Merchant,
        Payment, Verification,
    ]
    assert len(models) == 12
    for model in models:
        assert hasattr(model, "__tablename__")


def test_all_enums_importable():
    """All domain enums can be imported."""
    from app.models import (
        ActionStatus,
        ApprovalStatus,
        AssignmentGroup,
        AuditEventType,
        CaseStatus,
        ExperimentStatus,
        PaymentStatus,
        VerificationStatus,
    )

    enums = [
        ActionStatus, ApprovalStatus, AssignmentGroup, AuditEventType,
        CaseStatus, ExperimentStatus, PaymentStatus, VerificationStatus,
    ]
    assert len(enums) == 8


# ============================================================
# 2. Monetary columns use BigInteger
# ============================================================


def _get_column(model, column_name):
    """Get a column object from a SQLAlchemy model."""
    mapper = inspect(model)
    for col in mapper.columns:
        if col.name == column_name:
            return col
    raise ValueError(f"Column {column_name!r} not found on {model.__tablename__}")


def _assert_bigint(model, column_name):
    """Assert that a column uses BigInteger, not Float."""
    col = _get_column(model, column_name)
    assert isinstance(col.type, BigInteger), (
        f"{model.__tablename__}.{column_name} must use BigInteger, "
        f"got {type(col.type).__name__}. "
        f"Frozen architecture: integer minor units for money."
    )


def test_payment_amount_is_biginteger():
    from app.models import Payment
    _assert_bigint(Payment, "amount_minor")


def test_case_amount_at_risk_is_biginteger():
    from app.models import Case
    _assert_bigint(Case, "amount_at_risk_minor")


def test_intervention_monetary_fields_are_biginteger():
    from app.models import Intervention
    monetary_cols = [
        "recoverable_amount_minor",
        "intervention_cost_minor",
        "risk_penalty_minor",
        "expected_recovery_value_minor",
    ]
    for col_name in monetary_cols:
        _assert_bigint(Intervention, col_name)


def test_verification_recovered_amount_is_biginteger():
    from app.models import Verification
    _assert_bigint(Verification, "recovered_amount_minor")


def test_no_float_monetary_columns():
    """Scan ALL models for columns ending in '_minor' and verify BigInteger."""
    from app.models import (
        Action, AIDiagnosis, Approval, AuditEvent, Case, CaseContext,
        Experiment, ExperimentAssignment, Intervention, Merchant,
        Payment, Verification,
    )

    all_models = [
        Action, AIDiagnosis, Approval, AuditEvent, Case, CaseContext,
        Experiment, ExperimentAssignment, Intervention, Merchant,
        Payment, Verification,
    ]

    violations = []
    for model in all_models:
        mapper = inspect(model)
        for col in mapper.columns:
            if col.name.endswith("_minor"):
                if not isinstance(col.type, (BigInteger, Integer)):
                    violations.append(
                        f"{model.__tablename__}.{col.name}: {type(col.type).__name__}"
                    )

    assert not violations, (
        f"Monetary columns must use BigInteger. Violations: {violations}"
    )


# ============================================================
# 3. Idempotency key uniqueness
# ============================================================


def test_action_idempotency_key_is_unique():
    """actions.idempotency_key must have a DB-level UNIQUE constraint."""
    from app.models import Action

    col = _get_column(Action, "idempotency_key")
    assert col.unique is True, (
        "actions.idempotency_key MUST have a database-level UNIQUE constraint. "
        "Frozen architecture: application-level checks alone are NOT sufficient."
    )


def test_action_idempotency_key_is_indexed():
    """actions.idempotency_key must be indexed for lookup performance."""
    from app.models import Action

    col = _get_column(Action, "idempotency_key")
    assert col.index is True, "actions.idempotency_key should be indexed."


def test_action_idempotency_key_is_not_nullable():
    """actions.idempotency_key must not be nullable."""
    from app.models import Action

    col = _get_column(Action, "idempotency_key")
    assert col.nullable is False, "actions.idempotency_key must not be nullable."


# ============================================================
# 4. Foreign keys
# ============================================================


def _get_fk_targets(model):
    """Get all foreign key target table.column strings for a model."""
    mapper = inspect(model)
    fks = set()
    for col in mapper.columns:
        for fk in col.foreign_keys:
            fks.add(str(fk.target_fullname))
    return fks


def test_payment_fk_to_merchant():
    from app.models import Payment
    fks = _get_fk_targets(Payment)
    assert "merchants.id" in fks


def test_case_fk_to_merchant_and_payment():
    from app.models import Case
    fks = _get_fk_targets(Case)
    assert "merchants.id" in fks
    assert "payments.id" in fks


def test_case_context_fk_to_case():
    from app.models import CaseContext
    fks = _get_fk_targets(CaseContext)
    assert "cases.id" in fks


def test_ai_diagnosis_fk_to_case():
    from app.models import AIDiagnosis
    fks = _get_fk_targets(AIDiagnosis)
    assert "cases.id" in fks


def test_intervention_fk_to_case_and_diagnosis():
    from app.models import Intervention
    fks = _get_fk_targets(Intervention)
    assert "cases.id" in fks
    assert "ai_diagnoses.id" in fks


def test_action_fk_to_case_and_intervention():
    from app.models import Action
    fks = _get_fk_targets(Action)
    assert "cases.id" in fks
    assert "interventions.id" in fks


def test_approval_fk_to_action_and_case():
    from app.models import Approval
    fks = _get_fk_targets(Approval)
    assert "actions.id" in fks
    assert "cases.id" in fks


def test_verification_fk_to_action_case_payment():
    from app.models import Verification
    fks = _get_fk_targets(Verification)
    assert "actions.id" in fks
    assert "cases.id" in fks
    assert "payments.id" in fks


def test_experiment_assignment_fk_to_experiment_and_case():
    from app.models import ExperimentAssignment
    fks = _get_fk_targets(ExperimentAssignment)
    assert "experiments.id" in fks
    assert "cases.id" in fks


# ============================================================
# 5. Audit immutability
# ============================================================


def test_audit_event_has_no_updated_at():
    """AuditEvent must NOT have an updated_at column (append-only)."""
    from app.models import AuditEvent

    mapper = inspect(AuditEvent)
    column_names = {col.name for col in mapper.columns}
    assert "updated_at" not in column_names, (
        "AuditEvent must NOT have an updated_at column. "
        "Audit records are append-only and immutable."
    )


def test_audit_event_has_created_at():
    """AuditEvent must have a created_at column."""
    from app.models import AuditEvent

    mapper = inspect(AuditEvent)
    column_names = {col.name for col in mapper.columns}
    assert "created_at" in column_names


def test_audit_event_blocks_update():
    """AuditEvent ORM update listener should raise RuntimeError."""
    from app.models.audit_event import _audit_event_before_update, AuditEvent

    with pytest.raises(RuntimeError, match="immutable"):
        _audit_event_before_update(None, None, AuditEvent())


def test_audit_event_blocks_delete():
    """AuditEvent ORM delete listener should raise RuntimeError."""
    from app.models.audit_event import _audit_event_before_delete, AuditEvent

    with pytest.raises(RuntimeError, match="immutable"):
        _audit_event_before_delete(None, None, AuditEvent())


# ============================================================
# 6. Enum values
# ============================================================


def test_payment_status_values():
    from app.models.enums import PaymentStatus
    values = {s.value for s in PaymentStatus}
    assert values == {"pending", "authorized", "captured", "failed", "refunded"}


def test_case_status_values():
    from app.models.enums import CaseStatus
    values = {s.value for s in CaseStatus}
    expected = {
        "detected", "enriched", "diagnosed", "intervention_planned",
        "action_pending", "action_approved", "action_executing",
        "action_executed", "verifying", "recovered", "not_recovered",
        "closed", "stopped",
    }
    assert values == expected


def test_assignment_group_values():
    from app.models.enums import AssignmentGroup
    values = {s.value for s in AssignmentGroup}
    assert values == {"treatment", "holdout"}


def test_action_status_values():
    from app.models.enums import ActionStatus
    values = {s.value for s in ActionStatus}
    expected = {
        "planned", "pending_approval", "approved", "rejected",
        "executing", "executed", "failed", "cancelled",
    }
    assert values == expected


def test_approval_status_values():
    from app.models.enums import ApprovalStatus
    values = {s.value for s in ApprovalStatus}
    assert values == {"pending", "approved", "rejected", "expired"}


def test_verification_status_values():
    from app.models.enums import VerificationStatus
    values = {s.value for s in VerificationStatus}
    expected = {
        "pending", "verified_recovered", "verified_not_recovered",
        "verification_failed", "inconclusive",
    }
    assert values == expected


def test_experiment_status_values():
    from app.models.enums import ExperimentStatus
    values = {s.value for s in ExperimentStatus}
    assert values == {"draft", "active", "paused", "completed", "archived"}


def test_audit_event_type_values():
    from app.models.enums import AuditEventType
    values = {s.value for s in AuditEventType}
    expected = {
        "case_created", "case_enriched", "diagnosis_completed",
        "intervention_generated", "action_planned", "approval_requested",
        "approval_decided", "action_executed", "verification_completed",
        "experiment_assigned", "policy_evaluated", "demo_reset_executed",
    }
    assert values == expected


# ============================================================
# 7. Treatment/holdout support
# ============================================================


def test_experiment_assignment_supports_treatment():
    from app.models.enums import AssignmentGroup
    assert AssignmentGroup.TREATMENT.value == "treatment"


def test_experiment_assignment_supports_holdout():
    from app.models.enums import AssignmentGroup
    assert AssignmentGroup.HOLDOUT.value == "holdout"


def test_case_has_assignment_group_column():
    from app.models import Case
    col = _get_column(Case, "assignment_group")
    assert col.nullable is True, "assignment_group should be nullable (set before AI)"


# ============================================================
# 8. Experiment assignment uniqueness
# ============================================================


def test_experiment_assignment_has_composite_unique():
    """ExperimentAssignment must have unique(experiment_id, case_id)."""
    from app.models import ExperimentAssignment

    table = ExperimentAssignment.__table__
    unique_constraints = [
        c for c in table.constraints
        if hasattr(c, "columns") and len(c.columns) > 1
    ]

    found = False
    for uc in unique_constraints:
        col_names = {col.name for col in uc.columns}
        if col_names == {"experiment_id", "case_id"}:
            found = True
            break

    assert found, (
        "ExperimentAssignment must have a UniqueConstraint on "
        "(experiment_id, case_id) to prevent duplicate assignments."
    )


# ============================================================
# 9. AI confidence vs recovery probability (WARNING-03)
# ============================================================


def test_ai_diagnosis_has_separate_confidence_and_probability():
    """ai_confidence and recovery_probability must be separate columns."""
    from app.models import AIDiagnosis

    mapper = inspect(AIDiagnosis)
    column_names = {col.name for col in mapper.columns}

    assert "ai_confidence" in column_names, (
        "AIDiagnosis must have an ai_confidence column"
    )
    assert "recovery_probability" in column_names, (
        "AIDiagnosis must have a separate recovery_probability column"
    )

    confidence_col = _get_column(AIDiagnosis, "ai_confidence")
    probability_col = _get_column(AIDiagnosis, "recovery_probability")

    assert isinstance(confidence_col.type, Float), (
        "ai_confidence should be Float (raw AI score, not money)"
    )
    assert isinstance(probability_col.type, Float), (
        "recovery_probability should be Float (calibrated probability, not money)"
    )

    # They must be distinct columns
    assert confidence_col is not probability_col, (
        "ai_confidence and recovery_probability must be separate columns"
    )


def test_intervention_uses_calibrated_probability_not_ai_confidence():
    """Verify Intervention has estimated_recovery_probability_bps and no ai_confidence."""
    from app.models import Intervention
    mapper = inspect(Intervention)
    cols = {c.key for c in mapper.columns}

    # Must use the new integer bps representation
    assert "estimated_recovery_probability_bps" in cols
    # Ensure it's not float
    assert isinstance(mapper.columns["estimated_recovery_probability_bps"].type, Integer)

    assert "ai_confidence" not in cols, "AI confidence belongs to AIDiagnosis, not Intervention"


# ============================================================
# 10. Table names
# ============================================================


def test_table_names():
    """Verify expected table names for all 12 models."""
    from app.models import (
        Action, AIDiagnosis, Approval, AuditEvent, Case, CaseContext,
        Experiment, ExperimentAssignment, Intervention, Merchant,
        Payment, Verification,
    )

    expected = {
        "merchants", "payments", "cases", "case_contexts",
        "ai_diagnoses", "interventions", "actions", "approvals",
        "verifications", "experiments", "experiment_assignments",
        "audit_events",
    }

    actual = {
        Action.__tablename__, AIDiagnosis.__tablename__,
        Approval.__tablename__, AuditEvent.__tablename__,
        Case.__tablename__, CaseContext.__tablename__,
        Experiment.__tablename__, ExperimentAssignment.__tablename__,
        Intervention.__tablename__, Merchant.__tablename__,
        Payment.__tablename__, Verification.__tablename__,
    }

    assert actual == expected


# ============================================================
# 11. Migration structure
# ============================================================


def test_migration_module_importable():
    """Verify the migration using the actual Alembic CLI.

    This avoids Python import path shadowing issues with the local alembic/ directory.
    """
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "history"],
        capture_output=True,
        text=True,
        check=True
    )

    assert "001" in result.stdout
    assert "Initial schema" in result.stdout
