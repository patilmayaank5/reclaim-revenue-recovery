from dataclasses import dataclass

from app.models.enums import CaseStatus, PaymentStatus
from app.schemas.ingestion import NormalizedPaymentEvent


@dataclass
class RiskClassificationResult:
    """The result of deterministic risk classification."""
    is_at_risk: bool
    initial_status: CaseStatus | None
    failure_category: str | None


# List of failure codes/categories that are known to be definitively terminal.
# Trying to recover from these is pointless or prohibited.
TERMINAL_FAILURE_CODES = {
    "card_expired",
    "customer_cancelled",
    "fraud_suspected",
    "account_closed",
    "lost_card",
    "revoked_mandate",
}


def classify_risk(event: NormalizedPaymentEvent) -> RiskClassificationResult:
    """Deterministically classify a normalized payment event.

    This rule engine decides if the payment failure constitutes a revenue-at-risk Case,
    and if so, what the initial case status and failure category should be.
    """

    # If the payment was successful, it's not at risk
    if event.status in (PaymentStatus.CAPTURED.value, PaymentStatus.AUTHORIZED.value):
        return RiskClassificationResult(
            is_at_risk=False,
            initial_status=None,
            failure_category=None
        )

    # If it's still pending, it hasn't failed yet
    if event.status == PaymentStatus.PENDING.value:
        return RiskClassificationResult(
            is_at_risk=False,
            initial_status=None,
            failure_category=None
        )

    # For failed (or refunded) payments, we check if they are terminal.
    # Note: Refunds might technically be 'recovered' or not part of this pipeline,
    # but for Phase 2 we'll treat them safely.
    if event.status == PaymentStatus.FAILED.value:

        failure_code = event.failure_code or "unknown"

        if failure_code in TERMINAL_FAILURE_CODES:
            # It is a case, but it's immediately terminal/stopped.
            return RiskClassificationResult(
                is_at_risk=True,
                initial_status=CaseStatus.STOPPED,
                failure_category=failure_code
            )

        # Standard recoverable failure (insufficient funds, timeout, etc.)
        return RiskClassificationResult(
            is_at_risk=True,
            initial_status=CaseStatus.DETECTED,
            failure_category=failure_code
        )

    # Fallback for unexpected statuses
    return RiskClassificationResult(
        is_at_risk=False,
        initial_status=None,
        failure_category=None
    )
