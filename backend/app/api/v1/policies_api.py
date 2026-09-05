from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import get_db
from app.models.audit_event import AuditEvent
from app.models.enums import AuditEventType
from app.domain.policy.schemas import PolicyLimitsConfig, PolicyReasonCode, PolicyOutcome

router = APIRouter()

class PolicyCurrentResponse(BaseModel):
    policy_config: dict
    evaluation_rules: list[dict]
    reason_codes: list[str]
    outcome_types: list[str]
    recent_evaluations: list[dict]
    evaluation_summary: dict

@router.get("/current", response_model=PolicyCurrentResponse)
async def get_current_policy(session: AsyncSession = Depends(get_db)):
    """Current policy config + rule chain + recent evaluations."""
    # Policy Config Defaults
    config = PolicyLimitsConfig()

    # Reason Codes and Outcomes
    reason_codes = [r.value for r in PolicyReasonCode]
    outcome_types = [o.value for o in PolicyOutcome]

    # 7-Step Rules
    evaluation_rules = [
        {
            "precedence": 1,
            "rule": "Case & Assignment Safety Gates",
            "outcomes": "BLOCK",
            "description": "Holdout group, stopped cases, invalid assignment, missing diagnosis"
        },
        {
            "precedence": 2,
            "rule": "Economic Viability",
            "outcomes": "BLOCK",
            "description": "ERV ≤ 0 blocked"
        },
        {
            "precedence": 3,
            "rule": "Fraud / Risk Restrictions",
            "outcomes": "BLOCK",
            "description": "fraud_suspected + non-manual_review intervention blocked"
        },
        {
            "precedence": 4,
            "rule": "Maximum Recovery Ceiling",
            "outcomes": "BLOCK",
            "description": "Recoverable amount exceeds hard ceiling — overrides approval threshold"
        },
        {
            "precedence": 5,
            "rule": "Intervention-Specific Restrictions",
            "outcomes": "REQUIRE_APPROVAL",
            "description": "manual_review always requires human approval"
        },
        {
            "precedence": 6,
            "rule": "Human Approval Threshold",
            "outcomes": "REQUIRE_APPROVAL",
            "description": "Recoverable amount exceeds auto-approval threshold"
        },
        {
            "precedence": 7,
            "rule": "Auto-Execution Approval",
            "outcomes": "ALLOW_AUTO",
            "description": "All safety gates passed — eligible for automatic execution"
        }
    ]

    # Recent Evaluations
    recent_stmt = select(AuditEvent).where(
        AuditEvent.event_type == AuditEventType.POLICY_EVALUATED
    ).order_by(AuditEvent.created_at.desc()).limit(20)

    recent_res = await session.execute(recent_stmt)
    events = recent_res.scalars().all()

    recent_evaluations = []
    summary_counts = {
        "allow_auto": 0,
        "require_approval": 0,
        "block": 0,
        "total_evaluations": len(events)
    }

    for evt in events:
        data = evt.event_data or {}
        outcome = data.get("overall_outcome", "").lower()
        if outcome in summary_counts:
            summary_counts[outcome] += 1

        recent_evaluations.append({
            "case_id": str(evt.entity_id),
            "timestamp": evt.created_at.isoformat(),
            "overall_outcome": data.get("overall_outcome"),
            "selected_intervention_type": data.get("selected_intervention_type"),
            "reason_code": data.get("selected_reason_code"),
            "policy_version": data.get("policy_version"),
            "candidate_count": len(data.get("candidate_evaluations", []))
        })

    return PolicyCurrentResponse(
        policy_config={
            "policy_version": config.policy_version,
            "auto_approval_threshold_minor": config.auto_approval_threshold_minor,
            "max_recovery_limit_minor": config.max_recovery_limit_minor,
            "currency": "INR"
        },
        evaluation_rules=evaluation_rules,
        reason_codes=reason_codes,
        outcome_types=outcome_types,
        recent_evaluations=recent_evaluations,
        evaluation_summary={
            "total_evaluations": summary_counts["total_evaluations"],
            "allow_auto_count": summary_counts["allow_auto"],
            "require_approval_count": summary_counts["require_approval"],
            "block_count": summary_counts["block"]
        }
    )
