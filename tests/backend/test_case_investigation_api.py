import os
import uuid
import pytest
import asyncio
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/reclaim_test"
from app.main import app
from app.api.deps import get_db

from app.models.case import Case
from app.models.payment import Payment
from app.models.enums import CaseStatus, PaymentStatus

pytestmark = pytest.mark.asyncio

engine = create_async_engine(os.environ["DATABASE_URL"], echo=False, poolclass=NullPool)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with async_session() as session:
        yield session

@pytest.fixture(autouse=True)
def override_dependency():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

import pytest_asyncio

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture
async def db_session():
    async with async_session() as session:
        yield session
from app.models.enums import CaseStatus, PaymentStatus

@pytest.mark.asyncio
async def test_case_investigation_nonexistent(async_client: AsyncClient):
    """Verify that a genuinely nonexistent UUID returns HTTP 404."""
    fake_id = uuid.uuid4()
    response = await async_client.get(f"/api/v1/cases/{fake_id}/investigation")
    assert response.status_code == 404
    assert f"Case {fake_id} not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_case_investigation_detected_case(async_client: AsyncClient, db_session):
    """Verify that a DETECTED experiment case with no downstream data returns 200 safely."""
    # 0. Create Merchant
    merchant_id = uuid.uuid4()
    from app.models.merchant import Merchant
    merchant = Merchant(
        id=merchant_id,
        external_id=f"merch-{merchant_id}",
        name="Test Merchant",
        business_type="retail"
    )
    db_session.add(merchant)

    # 1. Create a Payment
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        merchant_id=merchant_id,
        external_id=f"pay-{payment_id}",
        amount_minor=5000,
        currency="INR",
        status=PaymentStatus.FAILED,
        payment_method="card",
        provider="simulator",
        attempted_at=datetime.now(timezone.utc)
    )
    db_session.add(payment)

    # 2. Create a Case in DETECTED state
    case_id = uuid.uuid4()
    case = Case(
        id=case_id,
        merchant_id=payment.merchant_id,
        payment_id=payment.id,
        status=CaseStatus.DETECTED,
        amount_at_risk_minor=payment.amount_minor,
        currency=payment.currency,
        failure_category=None,
        detected_at=datetime.now(timezone.utc)
    )
    db_session.add(case)
    await db_session.commit()

    # 3. Request investigation
    response = await async_client.get(f"/api/v1/cases/{case_id}/investigation")
    
    # 4. Assert
    assert response.status_code == 200
    data = response.json()
    
    # Check that Case identifier exactly matches Case.id
    assert data["case"]["id"] == str(case_id)
    
    # Check sections are present but safely empty
    assert data["payment"]["id"] == str(payment_id)
    assert data["diagnosis"] is None
    assert data["interventions"] == []
    assert data["action"] is None
    assert data["verification"] is None


@pytest.mark.asyncio
async def test_case_investigation_processed_case(async_client: AsyncClient, db_session):
    """Verify that a valid processed case returns investigation 200 with all sections."""
    from app.models.ai_diagnosis import AIDiagnosis
    from app.models.action import Action
    from app.models.intervention import Intervention
    from app.models.enums import ActionStatus
    from app.models.merchant import Merchant

    # 0. Create Merchant
    merchant_id = uuid.uuid4()
    merchant = Merchant(
        id=merchant_id,
        external_id=f"merch-proc-{merchant_id}",
        name="Test Merchant",
        business_type="retail"
    )
    db_session.add(merchant)

    # 1. Create dependencies
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        merchant_id=merchant_id,
        external_id=f"pay-proc-{payment_id}",
        amount_minor=8000,
        currency="INR",
        status=PaymentStatus.FAILED,
        payment_method="card",
        provider="simulator",
        attempted_at=datetime.now(timezone.utc)
    )
    db_session.add(payment)

    case_id = uuid.uuid4()
    case = Case(
        id=case_id,
        merchant_id=merchant_id,
        payment_id=payment.id,
        status=CaseStatus.ACTION_EXECUTED,
        amount_at_risk_minor=8000,
        currency="INR",
        failure_category="insufficient_funds",
        detected_at=datetime.now(timezone.utc)
    )
    db_session.add(case)

    # 2. Add AI Diagnosis
    diag = AIDiagnosis(
        id=uuid.uuid4(),
        case_id=case_id,
        diagnosis_category="insufficient_funds",
        ai_confidence=0.95,
        evidence={"reason": "Customer balance too low"},
        model_provider="fake-ai",
        model_name="test-model",
        prompt_version="1.0"
    )
    db_session.add(diag)

    # 3. Add Intervention
    inv_id = uuid.uuid4()
    inv = Intervention(
        id=inv_id,
        case_id=case_id,
        intervention_type="dynamic_routing",
        recoverable_amount_minor=8000,
        currency="INR",
        estimated_recovery_probability_bps=8000,
        intervention_cost_minor=50,
        risk_penalty_minor=0,
        expected_recovery_value_minor=6400,
        rank=1
    )
    db_session.add(inv)

    # 4. Add Action
    action = Action(
        id=uuid.uuid4(),
        case_id=case_id,
        intervention_id=inv_id,
        status=ActionStatus.EXECUTED,
        provider="simulator",
        idempotency_key=f"idemp-{uuid.uuid4()}"
    )
    db_session.add(action)
    await db_session.commit()

    # Request investigation
    response = await async_client.get(f"/api/v1/cases/{case_id}/investigation")
    
    assert response.status_code == 200
    data = response.json()
    assert data["case"]["id"] == str(case_id)
    assert data["payment"]["id"] == str(payment_id)
    assert data["diagnosis"]["diagnosis_category"] == "insufficient_funds"
    assert len(data["interventions"]) == 1
    assert data["interventions"][0]["intervention_type"] == "dynamic_routing"
    assert data["action"]["status"] == "executed"
