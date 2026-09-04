import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.case import Case
from app.models.case_context import CaseContext
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.services.enrichment import enrich_case


@pytest.fixture
def sample_data():
    merchant_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    case_id = uuid.uuid4()

    merchant = Merchant(
        id=merchant_id,
        business_type="saas"
    )
    payment = Payment(
        id=payment_id,
        merchant_id=merchant_id,
        amount_minor=10000,
        currency="USD",
        provider="demo",
        payment_method="card",
        failure_code="insufficient_funds",
        failure_description="Not enough money"
    )
    case = Case(
        id=case_id,
        merchant_id=merchant_id,
        payment_id=payment_id,
        detected_at=datetime.now(timezone.utc),
        failure_category="insufficient_funds"
    )

    return merchant, payment, case


@pytest.mark.asyncio
async def test_enrich_case_new(sample_data):
    merchant, payment, case = sample_data
    session = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from payments" in stmt_str:
            result.scalar_one.return_value = payment
        elif "from merchants" in stmt_str:
            result.scalar_one.return_value = merchant
        elif "from case_contexts" in stmt_str:
            result.scalar_one_or_none.return_value = None
        return result

    session.execute.side_effect = mock_execute

    context = await enrich_case(session, case)

    assert isinstance(context, CaseContext)
    assert context.case_id == case.id
    assert context.context_type == "enrichment_baseline"

    data = context.context_data
    assert data["merchant"]["business_type"] == "saas"
    assert data["payment"]["amount_minor"] == 10000
    assert data["payment"]["currency"] == "USD"
    assert data["payment"]["failure_code"] == "insufficient_funds"
    assert "case" in data

    # Assert it was added to session
    assert session.add.called
    added = session.add.call_args[0][0]
    assert added is context


@pytest.mark.asyncio
async def test_enrich_case_idempotent(sample_data):
    merchant, payment, case = sample_data
    session = AsyncMock()

    existing_context = CaseContext(
        id=uuid.uuid4(),
        case_id=case.id,
        context_type="enrichment_baseline",
        context_data={},
        source="internal"
    )

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from payments" in stmt_str:
            result.scalar_one.return_value = payment
        elif "from merchants" in stmt_str:
            result.scalar_one.return_value = merchant
        elif "from case_contexts" in stmt_str:
            result.scalar_one_or_none.return_value = existing_context
        return result

    session.execute.side_effect = mock_execute

    context = await enrich_case(session, case)

    assert context is existing_context
    assert context.context_data["payment"]["amount_minor"] == 10000

    # Assert we updated the existing object and added to session
    assert session.add.called
    added = session.add.call_args[0][0]
    assert added is existing_context
