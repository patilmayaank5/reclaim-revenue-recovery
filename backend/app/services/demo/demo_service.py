import logging
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.merchant import Merchant
from app.models.payment import Payment
from app.models.case import Case
from app.models.ingestion_event import IngestionEvent
from app.models.experiment import Experiment
from app.models.experiment_assignment import ExperimentAssignment
from app.models.intervention import Intervention
from app.models.action import Action
from app.models.approval import Approval
from app.models.verification import Verification
from app.models.ai_diagnosis import AIDiagnosis
from app.models.case_context import CaseContext
from app.models.audit_event import AuditEvent
from app.models.enums import AuditEventType, PaymentStatus

from app.schemas.ingestion import NormalizedPaymentEvent
from app.services.ingestion import process_payment_event
from app.services.ai_orchestrator import diagnose_case
from app.services.intervention_orchestrator import generate_and_rank_candidates
from app.services.experiment_assignment import assign_experiment
from app.services.action_service import create_action_for_case
from app.services.execution_service import execute_action
from app.services.verification_service import verify_action
from app.services.demo.scenarios import DemoScenarioDef, SCENARIOS
from app.domain.ai.provider import FakeAIProvider

logger = logging.getLogger(__name__)

DEMO_SEED = "reclaim-buildathon-v1"
DEMO_MERCHANT_EXTERNAL_ID = "demo_merchant_reclaim"

def get_deterministic_uuid(scenario_id: str, entity_name: str, index: int = 0) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"{DEMO_SEED}-{scenario_id}-{entity_name}-{index}")

async def get_or_create_demo_merchant(session: AsyncSession) -> Merchant:
    merchant_stmt = select(Merchant).where(Merchant.external_id == DEMO_MERCHANT_EXTERNAL_ID)
    res = await session.execute(merchant_stmt)
    merchant = res.scalar_one_or_none()
    if not merchant:
        merchant = Merchant(
            id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{DEMO_SEED}-merchant"),
            external_id=DEMO_MERCHANT_EXTERNAL_ID,
            name="Reclaim Demo Merchant",
            metadata_={"is_demo": True}
        )
        session.add(merchant)
        await session.commit()
    return merchant

async def reset_demo(session: AsyncSession):
    merchant = await get_or_create_demo_merchant(session)
    merchant_id = merchant.id

    # FK-compliant cascading deletion

    # 1. Get Cases and Payments
    payments_stmt = select(Payment.id).where(Payment.merchant_id == merchant_id)
    payments_res = await session.execute(payments_stmt)
    payment_ids = [p_id for p_id in payments_res.scalars()]

    cases_stmt = select(Case.id).where(Case.merchant_id == merchant_id)
    cases_res = await session.execute(cases_stmt)
    case_ids = [c_id for c_id in cases_res.scalars()]

    if case_ids:
        # Get Interventions and Actions
        inv_stmt = select(Intervention.id).where(Intervention.case_id.in_(case_ids))
        inv_res = await session.execute(inv_stmt)
        inv_ids = [i_id for i_id in inv_res.scalars()]

        if inv_ids:
            act_stmt = select(Action.id).where(Action.intervention_id.in_(inv_ids))
            act_res = await session.execute(act_stmt)
            act_ids = [a_id for a_id in act_res.scalars()]

            if act_ids:
                # Verifications and Approvals
                await session.execute(text("DELETE FROM verifications WHERE action_id = ANY(:a_ids)").bindparams(a_ids=act_ids))
                await session.execute(text("DELETE FROM approvals WHERE action_id = ANY(:a_ids)").bindparams(a_ids=act_ids))
                # Actions
                await session.execute(text("DELETE FROM actions WHERE id = ANY(:a_ids)").bindparams(a_ids=act_ids))

            # Interventions
            await session.execute(text("DELETE FROM interventions WHERE id = ANY(:i_ids)").bindparams(i_ids=inv_ids))

        # Case Dependencies
        await session.execute(text("DELETE FROM ai_diagnoses WHERE case_id = ANY(:c_ids)").bindparams(c_ids=case_ids))
        await session.execute(text("DELETE FROM case_contexts WHERE case_id = ANY(:c_ids)").bindparams(c_ids=case_ids))
        await session.execute(text("DELETE FROM experiment_assignments WHERE case_id = ANY(:c_ids)").bindparams(c_ids=case_ids))

    if payment_ids:
        await session.execute(text("DELETE FROM ingestion_events WHERE payment_id = ANY(:p_ids)").bindparams(p_ids=payment_ids))

    if case_ids:
        await session.execute(text("DELETE FROM cases WHERE merchant_id = :m_id").bindparams(m_id=merchant_id))

    if payment_ids:
        await session.execute(text("DELETE FROM payments WHERE merchant_id = :m_id").bindparams(m_id=merchant_id))

    # Deactivate all active experiments except the demo fixture
    exp_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{DEMO_SEED}-experiment")
    await session.execute(text("DELETE FROM experiment_assignments WHERE experiment_id = :demo_id").bindparams(demo_id=exp_id))
    await session.execute(text("UPDATE experiments SET status = 'completed' WHERE id != :demo_id AND status = 'active'").bindparams(demo_id=exp_id))


    # Emit reset audit event
    audit_event = AuditEvent(
        id=uuid.uuid4(),
        event_type=AuditEventType.DEMO_RESET_EXECUTED,
        entity_type="merchant",
        entity_id=merchant_id,
        actor="demo_service",
        event_data={"action": "DEMO_RESET_EXECUTED"}
    )
    session.add(audit_event)
    await session.commit()


async def run_scenario(session: AsyncSession, scenario_id: str) -> Dict[str, Any]:
    scenario = next((s for s in SCENARIOS if s.scenario_id == scenario_id), None)
    if not scenario:
        raise ValueError(f"Unknown scenario_id: {scenario_id}")

    merchant = await get_or_create_demo_merchant(session)

    if scenario.is_experiment:
        return await _run_experiment_scenario(session, scenario, merchant)
    else:
        return await _run_single_scenario(session, scenario, merchant)


async def _run_single_scenario(session: AsyncSession, scenario: DemoScenarioDef, merchant: Merchant) -> Dict[str, Any]:
    exp = await _get_or_create_demo_experiment(session)

    # Generate random UUIDs until we get one that hashes to Treatment
    while True:
        c_id = uuid.uuid4()
        bucket = _hash_bucket(str(exp.id), str(c_id))
        if bucket >= 10:
            break

    payment_ext_id = f"demo-pay-{c_id}"
    event_id = str(uuid.uuid4())

    event = NormalizedPaymentEvent(
        event_id=event_id,
        merchant_id=str(merchant.id),
        external_id=payment_ext_id,
        amount_minor=scenario.amount_minor,
        currency="INR",
        status=PaymentStatus.FAILED.value,
        payment_method="card",
        failure_code=scenario.failure_code,
        provider="simulator",
        event_timestamp=datetime.now(timezone.utc),
        external_metadata={"is_demo": True, "scenario": scenario.scenario_id}
    )

    # 1. Ingestion
    event.external_metadata["forced_case_id"] = str(c_id)
    ingest_res = await process_payment_event(session, event)
    case_id_str = ingest_res.case_id
    if not case_id_str:
        return {"scenario": scenario.name, "status": "No case generated (captured/pending?)"}

    actual_case_id = uuid.UUID(case_id_str)

    # Update the case_id to our deterministic one
    await session.execute(
        text("UPDATE cases SET id = :new_id WHERE id = :old_id").bindparams(new_id=c_id, old_id=actual_case_id)
    )

    # Fetch case
    res = await session.execute(select(Case).where(Case.id == c_id))
    case = res.scalar_one()

    # If case is stopped (e.g. revoked_mandate), we are done
    from app.models.enums import CaseStatus
    if case.status == CaseStatus.STOPPED:
        await session.commit()
        return {
            "scenario": scenario.name,
            "case_id": str(c_id),
            "final_status": "STOPPED",
            "message": "Terminal failure, no AI or action generated."
        }

    # Assign treatment
    await assign_experiment(session, case)

    # 2. AI Orchestrator
    try:
        await diagnose_case(session, case.id, provider=FakeAIProvider())
        await generate_and_rank_candidates(session, case.id)
    except Exception as e:
        logger.error(f"AI Orchestrator failed: {e}")

    # 3. Policy & Action
    try:
        action_res = await create_action_for_case(session, case.id)
    except Exception as e:
        return {"scenario": scenario.name, "case_id": case_id_str, "status": "blocked by policy", "error": str(e)}

    # Check if PENDING_APPROVAL
    if action_res.action and action_res.action.status.value == "pending_approval":
        await session.commit()
        return {
            "scenario": scenario.name,
            "case_id": case_id_str,
            "action_id": str(action_res.action.id),
            "final_status": "PENDING_APPROVAL",
            "message": "Waiting for human approval."
        }

    # 4. Execution
    try:
        await execute_action(session, action_res.action.id)
    except Exception as e:
        logger.error(f"Execution failed: {e}")

    # 5. Verification
    try:
        await verify_action(session, action_res.action.id)
    except Exception as e:
        logger.error(f"Verification failed: {e}")

    # Final fetch
    res = await session.execute(select(Case).where(Case.id == case.id))
    case = res.scalar_one()

    await session.commit()

    return {
        "scenario": scenario.name,
        "case_id": case_id_str,
        "final_status": case.status.value
    }


async def _get_or_create_demo_experiment(session: AsyncSession) -> Experiment:
    exp_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{DEMO_SEED}-experiment")
    res = await session.execute(select(Experiment).where(Experiment.id == exp_id))
    exp = res.scalar_one_or_none()
    if not exp:
        exp = Experiment(
            id=exp_id,
            name="Demo Fixture Experiment",
            description="Experiment for Buildathon Demo",
            status="active",
            intervention_strategy="smart_retry",
            holdout_percentage=10,
        )
        session.add(exp)
        await session.commit()
    return exp


def _hash_bucket(experiment_id: str, case_id: str) -> int:
    h = hashlib.sha256(f"{experiment_id}:{case_id}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 100


async def _run_experiment_scenario(session: AsyncSession, scenario: DemoScenarioDef, merchant: Merchant) -> Dict[str, Any]:
    exp = await _get_or_create_demo_experiment(session)

    # We need exactly 90 Treatment and 10 Holdout.
    # The holdout threshold is 10 (buckets 0-9).

    treatment_found = 0
    holdout_found = 0

    case_idx = 0

    treatment_case_ids = []
    holdout_case_ids = []

    # Find IDs
    while treatment_found < 90 or holdout_found < 10:
        c_id = uuid.uuid4()
        bucket = _hash_bucket(str(exp.id), str(c_id))

        if bucket < 10:
            if holdout_found < 10:
                holdout_case_ids.append(c_id)
                holdout_found += 1
        else:
            if treatment_found < 90:
                treatment_case_ids.append(c_id)
                treatment_found += 1

    all_cases = treatment_case_ids + holdout_case_ids

    treatment_recovered = 0
    holdout_recovered = 0

    for idx, c_id in enumerate(all_cases):
        # Pre-assign the ID for ingestion via external_id
        payment_ext_id = f"demo-exp-pay-{c_id}"
        event_id = str(uuid.uuid4())

        event = NormalizedPaymentEvent(
            event_id=event_id,
            merchant_id=str(merchant.id),
            external_id=payment_ext_id,
            amount_minor=scenario.amount_minor,
            currency="INR",
            status=PaymentStatus.FAILED.value,
            payment_method="card",
            failure_code=scenario.failure_code,
            provider="simulator",
            event_timestamp=datetime.now(timezone.utc),
            external_metadata={"is_demo": True, "scenario": scenario.scenario_id, "forced_case_id": str(c_id)}
        )

        # 1. Ingestion
        ingest_res = await process_payment_event(session, event)
        # Note: the real ingestion assigns a random case_id.
        # The SHA256 bucket depends on `case_id`. If `ingestion` assigns random UUID, we can't control it.
        # Let's forcibly override the case ID.
        if ingest_res.case_id:
            actual_case_id = uuid.UUID(ingest_res.case_id)
            # Update the case_id to our deterministic one
            await session.execute(
                text("UPDATE cases SET id = :new_id WHERE id = :old_id").bindparams(new_id=c_id, old_id=actual_case_id)
            )

            # Fetch case
            case_stmt = select(Case).where(Case.id == c_id)
            case_res = await session.execute(case_stmt)
            case_obj = case_res.scalar_one()

            # Now assign it
            await assign_experiment(session, case_obj)

            # Check bucket
            assignment_res = await session.execute(select(ExperimentAssignment).where(ExperimentAssignment.case_id == c_id))
            assignment = assignment_res.scalar_one()

            from app.models.enums import AssignmentGroup
            if assignment.group == AssignmentGroup.TREATMENT:
                # Flow AI and execution
                try:
                    await diagnose_case(session, c_id, provider=FakeAIProvider())
                    await generate_and_rank_candidates(session, c_id)
                    action = await create_action_for_case(session, c_id)
                    # First 45 treatment cases recover, remaining 45 do not
                    if treatment_recovered < 45 and action and action.action:
                        await execute_action(session, action.action.id)
                        await verify_action(session, action.action.id)
                        treatment_recovered += 1
                except Exception as e:
                    logger.warning(f"Scenario 4 treatment processing error for case {c_id}: {e}")
            elif assignment.group == AssignmentGroup.HOLDOUT:
                # No AI, no action
                # First 2 holdout cases naturally recover
                if holdout_recovered < 2:
                    # Natural recovery = ingest a CAPTURED event
                    cap_event = NormalizedPaymentEvent(
                        event_id=str(uuid.uuid4()),
                        merchant_id=str(merchant.id),
                        external_id=payment_ext_id,
                        amount_minor=scenario.amount_minor,
                        currency="INR",
                        status=PaymentStatus.CAPTURED.value,
                        payment_method="card",
                        provider="simulator",
                        event_timestamp=datetime.now(timezone.utc),
                    )
                    await process_payment_event(session, cap_event)
                    holdout_recovered += 1

    # Ensure any dangling transaction from the iteration is committed
    await session.commit()

    logger.info(f"Scenario 4 complete: treatment_recovered={treatment_recovered}, holdout_recovered={holdout_recovered}")

    return {
        "scenario": scenario.name,
        "message": "Experiment 4 seeded."
    }
