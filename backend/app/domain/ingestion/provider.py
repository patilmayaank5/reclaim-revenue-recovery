from abc import ABC, abstractmethod
from typing import Any, Dict

from app.schemas.ingestion import NormalizedPaymentEvent


class PaymentEventSource(ABC):
    """Abstract base class for provider payment event ingestion.

    All specific provider integrations (e.g. Razorpay, Stripe) must
    implement this interface to translate their raw payloads into the
    canonical NormalizedPaymentEvent.
    """

    @abstractmethod
    def normalize_payload(self, raw_payload: Dict[str, Any]) -> NormalizedPaymentEvent:
        """Parse and normalize a provider-specific webhook/event payload."""
        pass


class DemoPaymentEventSource(PaymentEventSource):
    """Deterministic synthetic provider for Phase 2 testing.

    Expects a payload matching NormalizedPaymentEvent closely,
    but demonstrates the translation boundary.
    """

    def normalize_payload(self, raw_payload: Dict[str, Any]) -> NormalizedPaymentEvent:
        # In a real provider, this would map raw keys (e.g. razorpay amount in paise)
        # to our normalized model. Here we just validate.
        # We rename `amount` to `amount_minor` to demonstrate normalization.
        amount = raw_payload.get("amount") or raw_payload.get("amount_minor")

        return NormalizedPaymentEvent(
            event_id=raw_payload["event_id"],
            external_id=raw_payload["external_id"],
            merchant_id=raw_payload["merchant_id"],
            amount_minor=int(amount),
            currency=raw_payload["currency"],
            status=raw_payload["status"],
            provider="demo_provider",
            failure_code=raw_payload.get("failure_code"),
            event_timestamp=raw_payload["event_timestamp"],
        )
