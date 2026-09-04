from datetime import datetime, timezone

from app.domain.providers.base import (
    ExecutionProvider,
    ExecutionRequest,
    ExecutionResponse,
    ExecutionResultStatus,
    VerificationRequest,
    VerificationResponse,
)
from app.models.enums import VerificationStatus


class SimulatorProvider(ExecutionProvider):
    """Deterministic Simulator Provider for local testing and Buildathon demos.

    Driven 100% deterministically by `request.metadata.get("simulator_scenario")`
    or failure categories. Zero random numbers or non-deterministic logic.
    """

    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        scenario = request.metadata.get("simulator_scenario", "success").lower().strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        if scenario == "success":
            return ExecutionResponse(
                status=ExecutionResultStatus.SUCCESS,
                provider_transaction_id=f"sim_tx_{request.idempotency_key[-8:]}",
                error_code=None,
                error_class=None,
                requires_verification=False,
                ambiguous=False,
                attempt_timestamp=now_iso,
            )
        elif scenario == "transient_failure":
            return ExecutionResponse(
                status=ExecutionResultStatus.TRANSIENT_FAILURE,
                provider_transaction_id=None,
                error_code="SIM_503_SERVICE_UNAVAILABLE",
                error_class="transient_network_error",
                requires_verification=False,
                ambiguous=False,
                attempt_timestamp=now_iso,
            )
        elif scenario == "permanent_failure":
            return ExecutionResponse(
                status=ExecutionResultStatus.PERMANENT_FAILURE,
                provider_transaction_id=None,
                error_code="SIM_400_CARD_EXPIRED",
                error_class="permanent_rejection",
                requires_verification=False,
                ambiguous=False,
                attempt_timestamp=now_iso,
            )
        elif scenario == "timeout":
            return ExecutionResponse(
                status=ExecutionResultStatus.AMBIGUOUS_TIMEOUT,
                provider_transaction_id=None,
                error_code="SIM_504_GATEWAY_TIMEOUT",
                error_class="ambiguous_network_timeout",
                requires_verification=True,
                ambiguous=True,
                attempt_timestamp=now_iso,
            )
        else:
            # Default fallback for unhandled custom scenarios is success
            return ExecutionResponse(
                status=ExecutionResultStatus.SUCCESS,
                provider_transaction_id=f"sim_tx_{request.idempotency_key[-8:]}",
                error_code=None,
                error_class=None,
                requires_verification=False,
                ambiguous=False,
                attempt_timestamp=now_iso,
            )

    async def verify(self, request: "VerificationRequest") -> "VerificationResponse":
        scenario = (
            request.metadata.get("verification_scenario")
            or request.metadata.get("simulator_scenario")
            or request.metadata.get("execution_outcome")
            or "recovered"
        ).lower().strip()

        now_iso = datetime.now(timezone.utc).isoformat()

        if scenario in ("recovered", "success"):
            return VerificationResponse(
                status=VerificationStatus.VERIFIED_RECOVERED,
                observed_payment_status="captured",
                recovered_amount_minor=request.amount_minor,
                currency=request.currency,
                provider_event_id=f"evt_rec_{request.action_id.hex[:8]}",
                provider_event_data={"provider_status": "captured", "event_type": "payment.captured"},
                verified_at=now_iso,
            )
        elif scenario in ("not_recovered", "permanent_failure", "transient_failure"):
            return VerificationResponse(
                status=VerificationStatus.VERIFIED_NOT_RECOVERED,
                observed_payment_status="failed",
                recovered_amount_minor=None,
                currency=request.currency,
                provider_event_id=f"evt_fail_{request.action_id.hex[:8]}",
                provider_event_data={"provider_status": "failed", "event_type": "payment.failed"},
                verified_at=now_iso,
            )
        elif scenario in ("pending", "timeout"):
            return VerificationResponse(
                status=VerificationStatus.PENDING,
                observed_payment_status="pending",
                recovered_amount_minor=None,
                currency=request.currency,
                provider_event_id=None,
                provider_event_data={"provider_status": "pending"},
                verified_at=now_iso,
            )
        elif scenario == "verification_failed":
            return VerificationResponse(
                status=VerificationStatus.VERIFICATION_FAILED,
                observed_payment_status=None,
                recovered_amount_minor=None,
                currency=request.currency,
                provider_event_id=None,
                provider_event_data=None,
                verified_at=now_iso,
            )
        else:
            return VerificationResponse(
                status=VerificationStatus.VERIFIED_RECOVERED,
                observed_payment_status="captured",
                recovered_amount_minor=request.amount_minor,
                currency=request.currency,
                provider_event_id=f"evt_rec_{request.action_id.hex[:8]}",
                provider_event_data={"provider_status": "captured"},
                verified_at=now_iso,
            )
