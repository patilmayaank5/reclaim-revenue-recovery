"""Deterministic seed data for Reclaim development/testing.

This script creates synthetic demo data for the Reclaim revenue recovery engine.
All data is clearly synthetic and does NOT represent real Razorpay production data.

Seed data is:
- Deterministic: uses fixed UUIDs and timestamps
- Repeatable: produces identical data on every run
- Comprehensive: covers the full recovery pipeline lifecycle

Usage:
    python -m scripts.seed
"""

import uuid
from datetime import datetime, timezone

# ============================================================
# FIXED UUIDs â€” deterministic, never random
# ============================================================

# Merchants
MERCHANT_ACME = uuid.UUID("00000000-0000-4000-a000-000000000001")
MERCHANT_GLOBEX = uuid.UUID("00000000-0000-4000-a000-000000000002")
MERCHANT_INITECH = uuid.UUID("00000000-0000-4000-a000-000000000003")

# Payments
PAY_ACME_FAIL_1 = uuid.UUID("00000000-0000-4000-b000-000000000001")
PAY_ACME_FAIL_2 = uuid.UUID("00000000-0000-4000-b000-000000000002")
PAY_ACME_CAPTURED = uuid.UUID("00000000-0000-4000-b000-000000000003")
PAY_GLOBEX_FAIL_1 = uuid.UUID("00000000-0000-4000-b000-000000000004")
PAY_GLOBEX_FAIL_2 = uuid.UUID("00000000-0000-4000-b000-000000000005")
PAY_INITECH_FAIL_1 = uuid.UUID("00000000-0000-4000-b000-000000000006")
PAY_INITECH_FAIL_2 = uuid.UUID("00000000-0000-4000-b000-000000000007")
PAY_INITECH_CAPTURED = uuid.UUID("00000000-0000-4000-b000-000000000008")

# Cases
CASE_ACME_RECOVERED = uuid.UUID("00000000-0000-4000-c000-000000000001")
CASE_ACME_APPROVAL = uuid.UUID("00000000-0000-4000-c000-000000000002")
CASE_GLOBEX_STOPPED = uuid.UUID("00000000-0000-4000-c000-000000000003")
CASE_GLOBEX_DETECTED = uuid.UUID("00000000-0000-4000-c000-000000000004")
CASE_INITECH_HOLDOUT = uuid.UUID("00000000-0000-4000-c000-000000000005")
CASE_INITECH_VERIFYING = uuid.UUID("00000000-0000-4000-c000-000000000006")

# Diagnoses
DIAG_ACME_1 = uuid.UUID("00000000-0000-4000-d000-000000000001")
DIAG_ACME_2 = uuid.UUID("00000000-0000-4000-d000-000000000002")
DIAG_GLOBEX_1 = uuid.UUID("00000000-0000-4000-d000-000000000003")
DIAG_INITECH_1 = uuid.UUID("00000000-0000-4000-d000-000000000004")

# Interventions
INTERV_ACME_RETRY = uuid.UUID("00000000-0000-4000-e000-000000000001")
INTERV_ACME_LINK = uuid.UUID("00000000-0000-4000-e000-000000000002")
INTERV_ACME_APPROVAL = uuid.UUID("00000000-0000-4000-e000-000000000003")
INTERV_GLOBEX_RETRY = uuid.UUID("00000000-0000-4000-e000-000000000004")
INTERV_INITECH_RETRY = uuid.UUID("00000000-0000-4000-e000-000000000005")

# Actions
ACTION_ACME_AUTO = uuid.UUID("00000000-0000-4000-f000-000000000001")
ACTION_ACME_HUMAN = uuid.UUID("00000000-0000-4000-f000-000000000002")
ACTION_GLOBEX_STOPPED = uuid.UUID("00000000-0000-4000-f000-000000000003")
ACTION_INITECH_VERIFY = uuid.UUID("00000000-0000-4000-f000-000000000004")

# Approvals
APPROVAL_ACME = uuid.UUID("00000000-0000-4000-f100-000000000001")

# Verifications
VERIF_ACME_SUCCESS = uuid.UUID("00000000-0000-4000-f200-000000000001")
VERIF_INITECH_PENDING = uuid.UUID("00000000-0000-4000-f200-000000000002")

# Experiments
EXP_RETRY_STRATEGY = uuid.UUID("00000000-0000-4000-f300-000000000001")
EXP_DUNNING_EMAIL = uuid.UUID("00000000-0000-4000-f300-000000000002")

# Experiment Assignments
ASSIGN_ACME_TREATMENT = uuid.UUID("00000000-0000-4000-f400-000000000001")
ASSIGN_GLOBEX_TREATMENT = uuid.UUID("00000000-0000-4000-f400-000000000002")
ASSIGN_INITECH_HOLDOUT = uuid.UUID("00000000-0000-4000-f400-000000000003")
ASSIGN_ACME_APPROVAL_T = uuid.UUID("00000000-0000-4000-f400-000000000004")
ASSIGN_INITECH_VERIFY_T = uuid.UUID("00000000-0000-4000-f400-000000000005")

# Audit Events
AUDIT_01 = uuid.UUID("00000000-0000-4000-f500-000000000001")
AUDIT_02 = uuid.UUID("00000000-0000-4000-f500-000000000002")
AUDIT_03 = uuid.UUID("00000000-0000-4000-f500-000000000003")
AUDIT_04 = uuid.UUID("00000000-0000-4000-f500-000000000004")
AUDIT_05 = uuid.UUID("00000000-0000-4000-f500-000000000005")
AUDIT_06 = uuid.UUID("00000000-0000-4000-f500-000000000006")
AUDIT_07 = uuid.UUID("00000000-0000-4000-f500-000000000007")
AUDIT_08 = uuid.UUID("00000000-0000-4000-f500-000000000008")
AUDIT_09 = uuid.UUID("00000000-0000-4000-f500-000000000009")
AUDIT_10 = uuid.UUID("00000000-0000-4000-f500-000000000010")

# Correlation ID
CORRELATION_ACME = uuid.UUID("00000000-0000-4000-f600-000000000001")
CORRELATION_GLOBEX = uuid.UUID("00000000-0000-4000-f600-000000000002")

# ============================================================
# FIXED TIMESTAMPS
# ============================================================
T0 = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 9, 1, 10, 5, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 9, 1, 10, 10, 0, tzinfo=timezone.utc)
T3 = datetime(2026, 9, 1, 10, 15, 0, tzinfo=timezone.utc)
T4 = datetime(2026, 9, 1, 10, 20, 0, tzinfo=timezone.utc)
T5 = datetime(2026, 9, 1, 10, 30, 0, tzinfo=timezone.utc)
T6 = datetime(2026, 9, 1, 10, 45, 0, tzinfo=timezone.utc)
T7 = datetime(2026, 9, 1, 11, 0, 0, tzinfo=timezone.utc)
T8 = datetime(2026, 9, 1, 11, 30, 0, tzinfo=timezone.utc)
T9 = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)


# ============================================================
# SEED DATA DICTIONARIES
# ============================================================

def get_merchants() -> list[dict]:
    """Return deterministic merchant seed data."""
    return [
        {
            "id": MERCHANT_ACME,
            "external_id": "demo_merchant_acme_001",
            "name": "Acme Corp (Demo)",
            "business_type": "e-commerce",
            "is_active": True,
            "metadata_": {"tier": "premium", "region": "IN", "demo": True},
            "created_at": T0,
            "updated_at": T0,
        },
        {
            "id": MERCHANT_GLOBEX,
            "external_id": "demo_merchant_globex_002",
            "name": "Globex Corp (Demo)",
            "business_type": "saas",
            "is_active": True,
            "metadata_": {"tier": "standard", "region": "IN", "demo": True},
            "created_at": T0,
            "updated_at": T0,
        },
        {
            "id": MERCHANT_INITECH,
            "external_id": "demo_merchant_initech_003",
            "name": "Initech Ltd (Demo)",
            "business_type": "subscription",
            "is_active": True,
            "metadata_": {"tier": "premium", "region": "US", "demo": True},
            "created_at": T0,
            "updated_at": T0,
        },
    ]


def get_payments() -> list[dict]:
    """Return deterministic payment seed data.

    All amounts are in integer minor units (paise for INR, cents for USD).
    """
    return [
        {
            "id": PAY_ACME_FAIL_1,
            "merchant_id": MERCHANT_ACME,
            "external_id": "demo_pay_acme_001",
            "amount_minor": 2500000,  # INR 25,000.00
            "currency": "INR",
            "status": "failed",
            "payment_method": "upi",
            "failure_code": "BANK_TIMEOUT",
            "failure_description": "Bank did not respond within timeout period",
            "provider": "demo",
            "external_metadata": {"demo": True},
            "attempted_at": T0,
            "created_at": T0,
            "updated_at": T0,
        },
        {
            "id": PAY_ACME_FAIL_2,
            "merchant_id": MERCHANT_ACME,
            "external_id": "demo_pay_acme_002",
            "amount_minor": 7500000,  # INR 75,000.00
            "currency": "INR",
            "status": "failed",
            "payment_method": "card",
            "failure_code": "INSUFFICIENT_FUNDS",
            "failure_description": "Card issuer declined due to insufficient funds",
            "provider": "demo",
            "external_metadata": {"demo": True},
            "attempted_at": T0,
            "created_at": T0,
            "updated_at": T0,
        },
        {
            "id": PAY_ACME_CAPTURED,
            "merchant_id": MERCHANT_ACME,
            "external_id": "demo_pay_acme_003",
            "amount_minor": 1500000,  # INR 15,000.00
            "currency": "INR",
            "status": "captured",
            "payment_method": "netbanking",
            "failure_code": None,
            "failure_description": None,
            "provider": "demo",
            "external_metadata": {"demo": True},
            "attempted_at": T0,
            "created_at": T0,
            "updated_at": T0,
        },
        {
            "id": PAY_GLOBEX_FAIL_1,
            "merchant_id": MERCHANT_GLOBEX,
            "external_id": "demo_pay_globex_001",
            "amount_minor": 499900,  # INR 4,999.00
            "currency": "INR",
            "status": "failed",
            "payment_method": "card",
            "failure_code": "CARD_EXPIRED",
            "failure_description": "Card has expired",
            "provider": "demo",
            "external_metadata": {"demo": True},
            "attempted_at": T0,
            "created_at": T0,
            "updated_at": T0,
        },
        {
            "id": PAY_GLOBEX_FAIL_2,
            "merchant_id": MERCHANT_GLOBEX,
            "external_id": "demo_pay_globex_002",
            "amount_minor": 120000,  # INR 1,200.00
            "currency": "INR",
            "status": "failed",
            "payment_method": "upi",
            "failure_code": "USER_CANCELLED",
            "failure_description": "User cancelled the payment",
            "provider": "demo",
            "external_metadata": {"demo": True},
            "attempted_at": T1,
            "created_at": T1,
            "updated_at": T1,
        },
        {
            "id": PAY_INITECH_FAIL_1,
            "merchant_id": MERCHANT_INITECH,
            "external_id": "demo_pay_initech_001",
            "amount_minor": 9999,  # USD 99.99
            "currency": "USD",
            "status": "failed",
            "payment_method": "card",
            "failure_code": "NETWORK_ERROR",
            "failure_description": "Network connectivity issue during processing",
            "provider": "demo",
            "external_metadata": {"demo": True},
            "attempted_at": T1,
            "created_at": T1,
            "updated_at": T1,
        },
        {
            "id": PAY_INITECH_FAIL_2,
            "merchant_id": MERCHANT_INITECH,
            "external_id": "demo_pay_initech_002",
            "amount_minor": 49999,  # USD 499.99
            "currency": "USD",
            "status": "failed",
            "payment_method": "card",
            "failure_code": "AUTHENTICATION_FAILED",
            "failure_description": "3DS authentication failed",
            "provider": "demo",
            "external_metadata": {"demo": True},
            "attempted_at": T1,
            "created_at": T1,
            "updated_at": T1,
        },
        {
            "id": PAY_INITECH_CAPTURED,
            "merchant_id": MERCHANT_INITECH,
            "external_id": "demo_pay_initech_003",
            "amount_minor": 29999,  # USD 299.99
            "currency": "USD",
            "status": "captured",
            "payment_method": "card",
            "failure_code": None,
            "failure_description": None,
            "provider": "demo",
            "external_metadata": {"demo": True},
            "attempted_at": T0,
            "created_at": T0,
            "updated_at": T0,
        },
    ]


def get_cases() -> list[dict]:
    """Return deterministic case seed data."""
    return [
        {
            "id": CASE_ACME_RECOVERED,
            "merchant_id": MERCHANT_ACME,
            "payment_id": PAY_ACME_FAIL_1,
            "status": "recovered",
            "amount_at_risk_minor": 2500000,
            "currency": "INR",
            "failure_category": "bank_timeout",
            "assignment_group": "treatment",
            "detected_at": T1,
            "resolved_at": T7,
            "created_at": T1,
            "updated_at": T7,
        },
        {
            "id": CASE_ACME_APPROVAL,
            "merchant_id": MERCHANT_ACME,
            "payment_id": PAY_ACME_FAIL_2,
            "status": "action_pending",
            "amount_at_risk_minor": 7500000,
            "currency": "INR",
            "failure_category": "insufficient_funds",
            "assignment_group": "treatment",
            "detected_at": T1,
            "resolved_at": None,
            "created_at": T1,
            "updated_at": T4,
        },
        {
            "id": CASE_GLOBEX_STOPPED,
            "merchant_id": MERCHANT_GLOBEX,
            "payment_id": PAY_GLOBEX_FAIL_1,
            "status": "stopped",
            "amount_at_risk_minor": 499900,
            "currency": "INR",
            "failure_category": "card_expired",
            "assignment_group": "treatment",
            "detected_at": T2,
            "resolved_at": T5,
            "created_at": T2,
            "updated_at": T5,
        },
        {
            "id": CASE_GLOBEX_DETECTED,
            "merchant_id": MERCHANT_GLOBEX,
            "payment_id": PAY_GLOBEX_FAIL_2,
            "status": "detected",
            "amount_at_risk_minor": 120000,
            "currency": "INR",
            "failure_category": "user_cancelled",
            "assignment_group": None,
            "detected_at": T3,
            "resolved_at": None,
            "created_at": T3,
            "updated_at": T3,
        },
        {
            "id": CASE_INITECH_HOLDOUT,
            "merchant_id": MERCHANT_INITECH,
            "payment_id": PAY_INITECH_FAIL_1,
            "status": "detected",
            "amount_at_risk_minor": 9999,
            "currency": "USD",
            "failure_category": "network_error",
            "assignment_group": "holdout",
            "detected_at": T2,
            "resolved_at": None,
            "created_at": T2,
            "updated_at": T2,
        },
        {
            "id": CASE_INITECH_VERIFYING,
            "merchant_id": MERCHANT_INITECH,
            "payment_id": PAY_INITECH_FAIL_2,
            "status": "verifying",
            "amount_at_risk_minor": 49999,
            "currency": "USD",
            "failure_category": "authentication_failed",
            "assignment_group": "treatment",
            "detected_at": T2,
            "resolved_at": None,
            "created_at": T2,
            "updated_at": T6,
        },
    ]


def get_case_contexts() -> list[dict]:
    """Return deterministic case context seed data."""
    return [
        {
            "id": uuid.UUID("00000000-0000-4000-c100-000000000001"),
            "case_id": CASE_ACME_RECOVERED,
            "context_type": "payment_history",
            "context_data": {
                "previous_attempts": 2,
                "success_rate": 0.85,
                "avg_amount_minor": 2000000,
                "demo": True,
            },
            "source": "enrichment_service",
            "created_at": T2,
        },
        {
            "id": uuid.UUID("00000000-0000-4000-c100-000000000002"),
            "case_id": CASE_ACME_RECOVERED,
            "context_type": "merchant_profile",
            "context_data": {
                "merchant_category": "e-commerce",
                "monthly_volume_minor": 50000000,
                "chargeback_rate": 0.002,
                "demo": True,
            },
            "source": "enrichment_service",
            "created_at": T2,
        },
        {
            "id": uuid.UUID("00000000-0000-4000-c100-000000000003"),
            "case_id": CASE_ACME_APPROVAL,
            "context_type": "payment_history",
            "context_data": {
                "previous_attempts": 1,
                "success_rate": 0.65,
                "avg_amount_minor": 5000000,
                "demo": True,
            },
            "source": "enrichment_service",
            "created_at": T2,
        },
    ]


def get_ai_diagnoses() -> list[dict]:
    """Return deterministic AI diagnosis seed data.

    IMPORTANT: ai_confidence is raw AI output.
    recovery_probability is a SEPARATE calibrated value.
    """
    return [
        {
            "id": DIAG_ACME_1,
            "case_id": CASE_ACME_RECOVERED,
            "diagnosis_category": "transient_bank_failure",
            "evidence": {
                "signals": ["bank_timeout", "first_attempt", "high_merchant_success_rate"],
                "summary": "Transient bank timeout. High likelihood of success on retry.",
                "demo": True,
            },
            "ai_confidence": 0.92,
            "recovery_probability": 0.78,  # Calibrated separately from AI confidence
            "model_provider": "anthropic",
            "model_name": "claude-sonnet-demo",
            "prompt_version": "v1.0-demo",
            "raw_response_metadata": {"demo": True, "tokens_used": 450},
            "created_at": T2,
        },
        {
            "id": DIAG_ACME_2,
            "case_id": CASE_ACME_APPROVAL,
            "diagnosis_category": "buyer_cash_flow",
            "evidence": {
                "signals": ["insufficient_funds", "high_amount", "card_payment"],
                "summary": "Buyer likely has temporary cash flow issue. Payment link recommended.",
                "demo": True,
            },
            "ai_confidence": 0.75,
            "recovery_probability": 0.45,  # Lower calibrated probability
            "model_provider": "anthropic",
            "model_name": "claude-sonnet-demo",
            "prompt_version": "v1.0-demo",
            "raw_response_metadata": {"demo": True, "tokens_used": 520},
            "created_at": T2,
        },
        {
            "id": DIAG_GLOBEX_1,
            "case_id": CASE_GLOBEX_STOPPED,
            "diagnosis_category": "expired_instrument",
            "evidence": {
                "signals": ["card_expired", "no_alternative_method"],
                "summary": "Card expired. No alternative payment method available. Unrecoverable.",
                "demo": True,
            },
            "ai_confidence": 0.95,
            "recovery_probability": 0.05,  # Very low probability
            "model_provider": "anthropic",
            "model_name": "claude-sonnet-demo",
            "prompt_version": "v1.0-demo",
            "raw_response_metadata": {"demo": True, "tokens_used": 380},
            "created_at": T3,
        },
        {
            "id": DIAG_INITECH_1,
            "case_id": CASE_INITECH_VERIFYING,
            "diagnosis_category": "authentication_issue",
            "evidence": {
                "signals": ["3ds_failed", "retry_with_different_flow"],
                "summary": "3DS auth failed. Alternative authentication flow may succeed.",
                "demo": True,
            },
            "ai_confidence": 0.82,
            "recovery_probability": 0.60,
            "model_provider": "anthropic",
            "model_name": "claude-sonnet-demo",
            "prompt_version": "v1.0-demo",
            "raw_response_metadata": {"demo": True, "tokens_used": 410},
            "created_at": T3,
        },
    ]


def get_interventions() -> list[dict]:
    """Return deterministic intervention seed data.

    All monetary values use integer minor units.
    ERV = P(recovery) * recoverable_amount - cost - risk_penalty
    """
    return [
        {
            "id": INTERV_ACME_RETRY,
            "case_id": CASE_ACME_RECOVERED,
            "diagnosis_id": DIAG_ACME_1,
            "intervention_type": "smart_retry",
            "recoverable_amount_minor": 2500000,
            "currency": "INR",
            "estimated_recovery_probability": 0.78,
            "intervention_cost_minor": 500,     # INR 5.00
            "risk_penalty_minor": 25000,         # INR 250.00
            # ERV = 0.78 * 2500000 - 500 - 25000 = 1950000 - 500 - 25000 = 1924500
            "expected_recovery_value_minor": 1924500,
            "rank": 1,
            "rationale": "Smart retry with optimized timing. High success probability.",
            "evidence": {"demo": True},
            "created_at": T3,
        },
        {
            "id": INTERV_ACME_LINK,
            "case_id": CASE_ACME_RECOVERED,
            "diagnosis_id": DIAG_ACME_1,
            "intervention_type": "payment_link",
            "recoverable_amount_minor": 2500000,
            "currency": "INR",
            "estimated_recovery_probability": 0.55,
            "intervention_cost_minor": 1000,
            "risk_penalty_minor": 50000,
            # ERV = 0.55 * 2500000 - 1000 - 50000 = 1375000 - 1000 - 50000 = 1324000
            "expected_recovery_value_minor": 1324000,
            "rank": 2,
            "rationale": "Payment link as fallback option.",
            "evidence": {"demo": True},
            "created_at": T3,
        },
        {
            "id": INTERV_ACME_APPROVAL,
            "case_id": CASE_ACME_APPROVAL,
            "diagnosis_id": DIAG_ACME_2,
            "intervention_type": "payment_link",
            "recoverable_amount_minor": 7500000,
            "currency": "INR",
            "estimated_recovery_probability": 0.45,
            "intervention_cost_minor": 1500,
            "risk_penalty_minor": 150000,
            # ERV = 0.45 * 7500000 - 1500 - 150000 = 3375000 - 1500 - 150000 = 3223500
            "expected_recovery_value_minor": 3223500,
            "rank": 1,
            "rationale": "High value requires human approval before sending payment link.",
            "evidence": {"demo": True},
            "created_at": T3,
        },
        {
            "id": INTERV_GLOBEX_RETRY,
            "case_id": CASE_GLOBEX_STOPPED,
            "diagnosis_id": DIAG_GLOBEX_1,
            "intervention_type": "smart_retry",
            "recoverable_amount_minor": 499900,
            "currency": "INR",
            "estimated_recovery_probability": 0.05,
            "intervention_cost_minor": 500,
            "risk_penalty_minor": 10000,
            # ERV = 0.05 * 499900 - 500 - 10000 = 24995 - 500 - 10000 = 14495
            "expected_recovery_value_minor": 14495,
            "rank": 1,
            "rationale": "Low probability. Card expired with no alternative.",
            "evidence": {"demo": True},
            "created_at": T3,
        },
        {
            "id": INTERV_INITECH_RETRY,
            "case_id": CASE_INITECH_VERIFYING,
            "diagnosis_id": DIAG_INITECH_1,
            "intervention_type": "smart_retry",
            "recoverable_amount_minor": 49999,
            "currency": "USD",
            "estimated_recovery_probability": 0.60,
            "intervention_cost_minor": 50,
            "risk_penalty_minor": 500,
            # ERV = 0.60 * 49999 - 50 - 500 = 29999 - 50 - 500 = 29449
            "expected_recovery_value_minor": 29449,
            "rank": 1,
            "rationale": "Retry with alternative authentication flow.",
            "evidence": {"demo": True},
            "created_at": T4,
        },
    ]


def get_actions() -> list[dict]:
    """Return deterministic action seed data."""
    return [
        {
            "id": ACTION_ACME_AUTO,
            "case_id": CASE_ACME_RECOVERED,
            "intervention_id": INTERV_ACME_RETRY,
            "status": "executed",
            "provider": "demo",
            "idempotency_key": "demo-action-acme-auto-001",
            "execution_metadata": {"demo": True, "auto_approved": True},
            "scheduled_at": T4,
            "executed_at": T5,
            "created_at": T4,
            "updated_at": T5,
        },
        {
            "id": ACTION_ACME_HUMAN,
            "case_id": CASE_ACME_APPROVAL,
            "intervention_id": INTERV_ACME_APPROVAL,
            "status": "pending_approval",
            "provider": "demo",
            "idempotency_key": "demo-action-acme-human-001",
            "execution_metadata": {"demo": True, "requires_approval": True},
            "scheduled_at": None,
            "executed_at": None,
            "created_at": T4,
            "updated_at": T4,
        },
        {
            "id": ACTION_GLOBEX_STOPPED,
            "case_id": CASE_GLOBEX_STOPPED,
            "intervention_id": INTERV_GLOBEX_RETRY,
            "status": "cancelled",
            "provider": "demo",
            "idempotency_key": "demo-action-globex-stopped-001",
            "execution_metadata": {"demo": True, "reason": "policy_stop"},
            "scheduled_at": T4,
            "executed_at": None,
            "created_at": T4,
            "updated_at": T5,
        },
        {
            "id": ACTION_INITECH_VERIFY,
            "case_id": CASE_INITECH_VERIFYING,
            "intervention_id": INTERV_INITECH_RETRY,
            "status": "executed",
            "provider": "demo",
            "idempotency_key": "demo-action-initech-verify-001",
            "execution_metadata": {"demo": True},
            "scheduled_at": T5,
            "executed_at": T6,
            "created_at": T5,
            "updated_at": T6,
        },
    ]


def get_approvals() -> list[dict]:
    """Return deterministic approval seed data."""
    return [
        {
            "id": APPROVAL_ACME,
            "action_id": ACTION_ACME_HUMAN,
            "case_id": CASE_ACME_APPROVAL,
            "status": "pending",
            "requested_at": T4,
            "decided_at": None,
            "approver_id": None,
            "decision_reason": None,
            "created_at": T4,
        },
    ]


def get_verifications() -> list[dict]:
    """Return deterministic verification seed data."""
    return [
        {
            "id": VERIF_ACME_SUCCESS,
            "action_id": ACTION_ACME_AUTO,
            "case_id": CASE_ACME_RECOVERED,
            "payment_id": PAY_ACME_FAIL_1,
            "status": "verified_recovered",
            "observed_payment_status": "captured",
            "recovered_amount_minor": 2500000,
            "currency": "INR",
            "provider_event_id": "demo_event_001",
            "provider_event_data": {"demo": True, "event": "payment.captured"},
            "verified_at": T6,
            "created_at": T6,
        },
        {
            "id": VERIF_INITECH_PENDING,
            "action_id": ACTION_INITECH_VERIFY,
            "case_id": CASE_INITECH_VERIFYING,
            "payment_id": PAY_INITECH_FAIL_2,
            "status": "pending",
            "observed_payment_status": None,
            "recovered_amount_minor": None,
            "currency": "USD",
            "provider_event_id": None,
            "provider_event_data": None,
            "verified_at": None,
            "created_at": T7,
        },
    ]


def get_experiments() -> list[dict]:
    """Return deterministic experiment seed data."""
    return [
        {
            "id": EXP_RETRY_STRATEGY,
            "name": "Smart Retry Timing (Demo)",
            "description": "Test optimized retry timing vs standard retry for bank timeout failures.",
            "segment_filter": {"failure_category": "bank_timeout", "demo": True},
            "intervention_strategy": "smart_retry",
            "status": "active",
            "holdout_percentage": 20,
            "started_at": T0,
            "completed_at": None,
            "created_at": T0,
            "updated_at": T0,
        },
        {
            "id": EXP_DUNNING_EMAIL,
            "name": "Dunning Email Effectiveness (Demo)",
            "description": "Measure effectiveness of AI-personalized dunning emails.",
            "segment_filter": {"failure_category": ["insufficient_funds", "authentication_failed"], "demo": True},
            "intervention_strategy": "dunning_email",
            "status": "draft",
            "holdout_percentage": 25,
            "started_at": None,
            "completed_at": None,
            "created_at": T0,
            "updated_at": T0,
        },
    ]


def get_experiment_assignments() -> list[dict]:
    """Return deterministic experiment assignment seed data."""
    return [
        {
            "id": ASSIGN_ACME_TREATMENT,
            "experiment_id": EXP_RETRY_STRATEGY,
            "case_id": CASE_ACME_RECOVERED,
            "group": "treatment",
            "assignment_hash": "sha256:demo:acme_recovered:retry_strategy:treatment",
            "assigned_at": T1,
            "created_at": T1,
        },
        {
            "id": ASSIGN_GLOBEX_TREATMENT,
            "experiment_id": EXP_RETRY_STRATEGY,
            "case_id": CASE_GLOBEX_STOPPED,
            "group": "treatment",
            "assignment_hash": "sha256:demo:globex_stopped:retry_strategy:treatment",
            "assigned_at": T2,
            "created_at": T2,
        },
        {
            "id": ASSIGN_INITECH_HOLDOUT,
            "experiment_id": EXP_RETRY_STRATEGY,
            "case_id": CASE_INITECH_HOLDOUT,
            "group": "holdout",
            "assignment_hash": "sha256:demo:initech_holdout:retry_strategy:holdout",
            "assigned_at": T2,
            "created_at": T2,
        },
        {
            "id": ASSIGN_ACME_APPROVAL_T,
            "experiment_id": EXP_RETRY_STRATEGY,
            "case_id": CASE_ACME_APPROVAL,
            "group": "treatment",
            "assignment_hash": "sha256:demo:acme_approval:retry_strategy:treatment",
            "assigned_at": T1,
            "created_at": T1,
        },
        {
            "id": ASSIGN_INITECH_VERIFY_T,
            "experiment_id": EXP_RETRY_STRATEGY,
            "case_id": CASE_INITECH_VERIFYING,
            "group": "treatment",
            "assignment_hash": "sha256:demo:initech_verifying:retry_strategy:treatment",
            "assigned_at": T2,
            "created_at": T2,
        },
    ]


def get_audit_events() -> list[dict]:
    """Return deterministic audit event seed data."""
    return [
        {
            "id": AUDIT_01,
            "event_type": "case_created",
            "entity_type": "case",
            "entity_id": CASE_ACME_RECOVERED,
            "actor": "system",
            "correlation_id": CORRELATION_ACME,
            "event_data": {"status": "detected", "amount_at_risk_minor": 2500000, "demo": True},
            "created_at": T1,
        },
        {
            "id": AUDIT_02,
            "event_type": "case_enriched",
            "entity_type": "case",
            "entity_id": CASE_ACME_RECOVERED,
            "actor": "enrichment_service",
            "correlation_id": CORRELATION_ACME,
            "event_data": {"context_types": ["payment_history", "merchant_profile"], "demo": True},
            "created_at": T2,
        },
        {
            "id": AUDIT_03,
            "event_type": "diagnosis_completed",
            "entity_type": "case",
            "entity_id": CASE_ACME_RECOVERED,
            "actor": "ai_orchestrator",
            "correlation_id": CORRELATION_ACME,
            "event_data": {"diagnosis_category": "transient_bank_failure", "ai_confidence": 0.92, "demo": True},
            "created_at": T2,
        },
        {
            "id": AUDIT_04,
            "event_type": "intervention_generated",
            "entity_type": "case",
            "entity_id": CASE_ACME_RECOVERED,
            "actor": "ai_orchestrator",
            "correlation_id": CORRELATION_ACME,
            "event_data": {"intervention_count": 2, "top_erv_minor": 1924500, "demo": True},
            "created_at": T3,
        },
        {
            "id": AUDIT_05,
            "event_type": "policy_evaluated",
            "entity_type": "action",
            "entity_id": ACTION_ACME_AUTO,
            "actor": "policy_engine",
            "correlation_id": CORRELATION_ACME,
            "event_data": {"decision": "auto_approve", "reason": "within_auto_approval_threshold", "demo": True},
            "created_at": T4,
        },
        {
            "id": AUDIT_06,
            "event_type": "action_executed",
            "entity_type": "action",
            "entity_id": ACTION_ACME_AUTO,
            "actor": "execution_engine",
            "correlation_id": CORRELATION_ACME,
            "event_data": {"provider": "demo", "intervention_type": "smart_retry", "demo": True},
            "created_at": T5,
        },
        {
            "id": AUDIT_07,
            "event_type": "verification_completed",
            "entity_type": "action",
            "entity_id": ACTION_ACME_AUTO,
            "actor": "verification_service",
            "correlation_id": CORRELATION_ACME,
            "event_data": {"status": "verified_recovered", "recovered_amount_minor": 2500000, "demo": True},
            "created_at": T6,
        },
        {
            "id": AUDIT_08,
            "event_type": "case_created",
            "entity_type": "case",
            "entity_id": CASE_GLOBEX_STOPPED,
            "actor": "system",
            "correlation_id": CORRELATION_GLOBEX,
            "event_data": {"status": "detected", "amount_at_risk_minor": 499900, "demo": True},
            "created_at": T2,
        },
        {
            "id": AUDIT_09,
            "event_type": "experiment_assigned",
            "entity_type": "case",
            "entity_id": CASE_INITECH_HOLDOUT,
            "actor": "experiment_engine",
            "correlation_id": None,
            "event_data": {"experiment": "Smart Retry Timing (Demo)", "group": "holdout", "demo": True},
            "created_at": T2,
        },
        {
            "id": AUDIT_10,
            "event_type": "approval_requested",
            "entity_type": "action",
            "entity_id": ACTION_ACME_HUMAN,
            "actor": "policy_engine",
            "correlation_id": CORRELATION_ACME,
            "event_data": {"reason": "amount_exceeds_auto_threshold", "amount_minor": 7500000, "demo": True},
            "created_at": T4,
        },
    ]


def get_all_seed_data() -> dict:
    """Return all seed data as a dictionary of entity -> records."""
    return {
        "merchants": get_merchants(),
        "payments": get_payments(),
        "cases": get_cases(),
        "case_contexts": get_case_contexts(),
        "ai_diagnoses": get_ai_diagnoses(),
        "interventions": get_interventions(),
        "actions": get_actions(),
        "approvals": get_approvals(),
        "verifications": get_verifications(),
        "experiments": get_experiments(),
        "experiment_assignments": get_experiment_assignments(),
        "audit_events": get_audit_events(),
    }
