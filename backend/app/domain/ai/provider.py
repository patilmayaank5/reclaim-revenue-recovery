from abc import ABC, abstractmethod
from app.domain.ai.schemas import AIDiagnosisOutput

class AIProviderError(Exception):
    """Base exception for AI provider failures."""
    pass

class AITransientError(AIProviderError):
    """Exception for transient errors (rate limit, timeout) that can be retried."""
    pass

class AINonRetryableError(AIProviderError):
    """Exception for non-retryable errors (auth, bad schema, etc)."""
    pass

class AIProvider(ABC):
    @abstractmethod
    async def diagnose(self, context_payload: dict) -> AIDiagnosisOutput:
        """Produces a structured diagnosis based on the explicitly allowlisted context payload."""
        pass


class FakeAIProvider(AIProvider):
    """Fake provider for unit testing without network requirements."""

    def __init__(self, should_fail_transient=False, should_fail_permanent=False):
        self.should_fail_transient = should_fail_transient
        self.should_fail_permanent = should_fail_permanent
        self.call_count = 0
        self.last_payload = None

    async def diagnose(self, context_payload: dict) -> AIDiagnosisOutput:
        self.call_count += 1
        self.last_payload = context_payload

        if self.should_fail_transient:
            raise AITransientError("Simulated transient timeout/rate-limit.")

        if self.should_fail_permanent:
            raise AINonRetryableError("Simulated non-retryable error (e.g. invalid auth).")

        # Return a safe deterministic fake output
        return AIDiagnosisOutput(
            diagnosis_category="insufficient_funds",
            reason="Fake diagnosis reason for testing.",
            ai_confidence=0.9,
            recovery_probability=0.5,
            evidence={"amount_minor": context_payload.get("amount_at_risk_minor")},
            uncertainty="No uncertainty in fake mode."
        )
