from datetime import datetime, timezone

from app.domain.risk.rules import classify_risk, TERMINAL_FAILURE_CODES
from app.models.enums import CaseStatus, PaymentStatus
from app.schemas.ingestion import NormalizedPaymentEvent


def _make_event(status: str, failure_code: str | None = None) -> NormalizedPaymentEvent:
    return NormalizedPaymentEvent(
        event_id="evt-123",
        external_id="ext-123",
        merchant_id="00000000-0000-0000-0000-000000000000",
        amount_minor=10000,
        currency="INR",
        status=status,
        provider="demo",
        failure_code=failure_code,
        event_timestamp=datetime.now(timezone.utc)
    )


def test_captured_payment_is_not_at_risk():
    event = _make_event(status=PaymentStatus.CAPTURED.value)
    result = classify_risk(event)
    assert not result.is_at_risk
    assert result.initial_status is None


def test_pending_payment_is_not_at_risk():
    event = _make_event(status=PaymentStatus.PENDING.value)
    result = classify_risk(event)
    assert not result.is_at_risk
    assert result.initial_status is None


def test_failed_payment_recoverable():
    event = _make_event(status=PaymentStatus.FAILED.value, failure_code="insufficient_funds")
    result = classify_risk(event)
    assert result.is_at_risk
    assert result.initial_status == CaseStatus.DETECTED
    assert result.failure_category == "insufficient_funds"


def test_failed_payment_terminal():
    terminal_code = list(TERMINAL_FAILURE_CODES)[0]
    event = _make_event(status=PaymentStatus.FAILED.value, failure_code=terminal_code)
    result = classify_risk(event)
    assert result.is_at_risk
    assert result.initial_status == CaseStatus.STOPPED
    assert result.failure_category == terminal_code
