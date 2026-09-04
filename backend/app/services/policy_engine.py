import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.policy.rules import evaluate_candidate_policy
from app.domain.policy.schemas import (
    CandidatePolicyEvaluation,
    CasePolicyDecision,
    PolicyLimitsConfig,
    PolicyOutcome,
    PolicyReasonCode,
)
from app.models.ai_diagnosis import AIDiagnosis
from app.models.audit_event import AuditEvent
from app.models.case import Case
from app.models.enums import AuditEventType
from app.models.intervention import Intervention


class PolicyEngineError(Exception):
    """Exception raised when policy evaluation fails or safety gates block execution."""
    pass


DEFAULT_POLICY_CONFIG = PolicyLimitsConfig()


async def evaluate_policy_for_case(
    session: AsyncSession,
    case_id: uuid.UUID,
    config: PolicyLimitsConfig = DEFAULT_POLICY_CONFIG,
) -> CasePolicyDecision:
    """Evaluates policy authorization for a case and all its intervention candidates.

    - Evaluates ALL candidates against policy rules.
    - Selects the top-ranked non-BLOCK candidate.
    - Logs a structured AuditEvent upon successful evaluation.
    - Does NOT create actions, execute payments, or mutate Case/Payment state.
    """
    # 1. Fetch Case
    case_stmt = select(Case).where(Case.id == case_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()

    if not case:
        raise PolicyEngineError(f"Case with ID {case_id} not found")

    # 2. Fetch AI Diagnosis
    diag_stmt = select(AIDiagnosis).where(AIDiagnosis.case_id == case_id)
    diag_res = await session.execute(diag_stmt)
    diagnosis = diag_res.scalar_one_or_none()

    # 3. Fetch Phase 5 Interventions
    interventions_stmt = (
        select(Intervention)
        .where(Intervention.case_id == case_id)
        .order_by(Intervention.rank.asc())
    )
    interventions_res = await session.execute(interventions_stmt)
    candidates = list(interventions_res.scalars().all())

    # 4. Evaluate all candidates through policy rules
    evaluations: list[CandidatePolicyEvaluation] = []

    if not candidates:
        # Case where Phase 5 produced zero candidates or case was gated prior
        decision = CasePolicyDecision(
            case_id=case_id,
            policy_version=config.policy_version,
            overall_outcome=PolicyOutcome.BLOCK,
            selected_candidate_id=None,
            selected_intervention_type=None,
            selected_reason_code=PolicyReasonCode.NO_CANDIDATES_AVAILABLE,
            candidate_evaluations=[],
        )
    else:
        # Evaluate EVERY candidate
        candidate_map: dict[uuid.UUID, Intervention] = {}
        for candidate in candidates:
            candidate_map[candidate.id] = candidate
            ev = evaluate_candidate_policy(candidate, case, diagnosis, config)
            evaluations.append(ev)

        # Filter non-BLOCK candidate evaluations
        eligible_evaluations = [ev for ev in evaluations if ev.outcome != PolicyOutcome.BLOCK]

        if not eligible_evaluations:
            # All candidates are BLOCKED
            decision = CasePolicyDecision(
                case_id=case_id,
                policy_version=config.policy_version,
                overall_outcome=PolicyOutcome.BLOCK,
                selected_candidate_id=None,
                selected_intervention_type=None,
                selected_reason_code=PolicyReasonCode.NO_ELIGIBLE_CANDIDATE,
                candidate_evaluations=evaluations,
            )
        else:
            # Select the non-BLOCK candidate with lowest Phase 5 rank (highest priority)
            eligible_evaluations.sort(
                key=lambda ev: candidate_map[ev.candidate_id].rank
            )
            winning_eval = eligible_evaluations[0]

            decision = CasePolicyDecision(
                case_id=case_id,
                policy_version=config.policy_version,
                overall_outcome=winning_eval.outcome,
                selected_candidate_id=winning_eval.candidate_id,
                selected_intervention_type=winning_eval.intervention_type,
                selected_reason_code=winning_eval.reason_code,
                candidate_evaluations=evaluations,
            )

    # 5. Create structured allowlisted AuditEvent
    audit_data: dict[str, Any] = {
        "policy_version": config.policy_version,
        "auto_approval_threshold_minor": config.auto_approval_threshold_minor,
        "max_recovery_limit_minor": config.max_recovery_limit_minor,
        "overall_outcome": decision.overall_outcome.value,
        "selected_candidate_id": str(decision.selected_candidate_id) if decision.selected_candidate_id else None,
        "selected_intervention_type": decision.selected_intervention_type,
        "selected_reason_code": decision.selected_reason_code.value,
        "candidate_evaluations": [
            {
                "candidate_id": str(ev.candidate_id),
                "intervention_type": ev.intervention_type,
                "recoverable_amount_minor": ev.recoverable_amount_minor,
                "probability_bps": ev.probability_bps,
                "expected_recovery_value_minor": ev.expected_recovery_value_minor,
                "intervention_cost_minor": ev.intervention_cost_minor,
                "risk_penalty_minor": ev.risk_penalty_minor,
                "outcome": ev.outcome.value,
                "reason_code": ev.reason_code.value,
            }
            for ev in decision.candidate_evaluations
        ],
    }

    audit_event = AuditEvent(
        id=uuid.uuid4(),
        event_type=AuditEventType.POLICY_EVALUATED,
        entity_type="case",
        entity_id=case_id,
        actor="policy_engine",
        event_data=audit_data,
    )
    session.add(audit_event)

    return decision
