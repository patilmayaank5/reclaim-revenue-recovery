import os
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from sqlalchemy.pool import NullPool

# Setup test DB URL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/reclaim_test"

from app.main import app
from app.api.deps import get_db
from app.models.merchant import Merchant
from app.models.case import Case
from app.models.payment import Payment
from app.models.audit_event import AuditEvent
from app.services.demo.demo_service import DEMO_MERCHANT_EXTERNAL_ID

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

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
async def db_session():
    async with async_session() as session:
        yield session

async def test_demo_scenarios_list(client: AsyncClient):
    res = await client.get("/api/v1/demo/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) == 4

async def test_demo_reset(client: AsyncClient, db_session: AsyncSession):
    # Just run it to ensure no FK errors
    res = await client.post("/api/v1/demo/reset")
    assert res.status_code == 200, res.text

    # Assert merchant exists
    merch_stmt = select(Merchant).where(Merchant.external_id == DEMO_MERCHANT_EXTERNAL_ID)
    merch = (await db_session.execute(merch_stmt)).scalar_one_or_none()
    assert merch is not None

    # Assert Audit event created
    audit_stmt = select(AuditEvent).where(AuditEvent.entity_id == merch.id).order_by(AuditEvent.id.desc())
    audit_event = (await db_session.execute(audit_stmt)).scalars().first()
    assert audit_event is not None
    assert audit_event.event_data.get("action") == "DEMO_RESET_EXECUTED"

async def test_demo_scenario_3_terminal(client: AsyncClient, db_session: AsyncSession):
    await client.post("/api/v1/demo/reset")
    res = await client.post("/api/v1/demo/scenarios/scenario_3/run")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["final_status"] == "STOPPED"

    case_id = data["case_id"]
    from app.models.intervention import Intervention
    from tests.backend.test_demo_mode import async_session
    async with async_session() as fresh_session:
        inv = (await fresh_session.execute(select(Intervention).where(Intervention.case_id == case_id))).scalars().all()
    assert len(inv) == 0

async def test_demo_scenario_2_approval(client: AsyncClient, db_session: AsyncSession):
    await client.post("/api/v1/demo/reset")
    res = await client.post("/api/v1/demo/scenarios/scenario_2/run")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["final_status"] == "PENDING_APPROVAL"
    assert "action_id" in data

    from app.models.action import Action
    from tests.backend.test_demo_mode import async_session
    async with async_session() as fresh_session:
        action = (await fresh_session.execute(select(Action).where(Action.id == data["action_id"]))).scalar_one()
    assert action.status.value == "pending_approval"

async def test_demo_scenario_1_auto(client: AsyncClient, db_session: AsyncSession):
    await client.post("/api/v1/demo/reset")
    res = await client.post("/api/v1/demo/scenarios/scenario_1/run")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["final_status"] == "recovered"

async def test_demo_scenario_4_experiment(client: AsyncClient, db_session: AsyncSession):
    await client.post("/api/v1/demo/reset")
    res = await client.post("/api/v1/demo/scenarios/scenario_4/run")
    assert res.status_code == 200, res.text

    from app.models.experiment import Experiment
    from app.services.demo.demo_service import DEMO_SEED
    import uuid
    exp_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{DEMO_SEED}-experiment")

    from app.services.experiment_aggregation import compute_experiment_detail
    from tests.backend.test_demo_mode import async_session
    async with async_session() as fresh_session:
        detail = await compute_experiment_detail(fresh_session, exp_id)

    t_metrics = detail.cohort_metrics["treatment"]
    h_metrics = detail.cohort_metrics["holdout"]

    assert t_metrics.case_count == 90
    assert h_metrics.case_count == 10

    assert t_metrics.recovered_count == 45
    assert h_metrics.recovered_count == 2

    assert t_metrics.recovery_rate_bps == 5000
    assert h_metrics.recovery_rate_bps == 2000

    inc = detail.incremental_metrics
    assert inc.incremental_recovered_cases == 27
    assert inc.incremental_recovery_amount_minor == 2_700_000
    assert inc.lift_bps == 3000
