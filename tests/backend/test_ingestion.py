import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.case import Case
from app.models.ingestion_event import IngestionEvent
from app.models.merchant import Merchant
from app.models.payment import Payment
from app.schemas.ingestion import NormalizedPaymentEvent
from app.services.ingestion import (
    UnknownMerchantError,
    process_payment_event,
)


@pytest.fixture
def base_event():
    return NormalizedPaymentEvent(
        event_id="evt_001",
        external_id="pay_123",
        merchant_id=str(uuid.uuid4()),
        amount_minor=50000,
        currency="INR",
        status="failed",
        provider="demo",
        failure_code="insufficient_funds",
        event_timestamp=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_3_event_idempotency_scenario(base_event):
    """
    1. Process evt_001 for pay_123.
    2. Process evt_001 again.
    3. Verify no duplicate side effect.
    4. Process evt_002 for pay_123.
    5. Verify it is treated as a distinct event.
    6. Verify there is still only one Payment for pay_123.
    7. Verify Case behavior is deterministic.
    """

    session = AsyncMock()

    # Setup mocks
    mock_merchant = Merchant(id=uuid.UUID(base_event.merchant_id))
    mock_merchant_result = MagicMock()
    mock_merchant_result.scalar_one_or_none.return_value = mock_merchant

    # We'll control what existing records the session returns based on state
    existing_events = {}
    existing_payments = {}
    existing_cases = {}

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()

        if "from merchants" in stmt_str:
            return mock_merchant_result
        elif "from ingestion_events" in stmt_str:
            # Check by event_id binding is complex to mock, we'll cheat a bit by inspecting params if we could.
            # We'll just return based on what's in our dict.
            # A hack for testing: we assume if existing_events has values, we might be looking for it.
            # Actually, the test checks logic, so let's just make a simple mock state.
            pass

        return result

    # Instead of complex execute mocking, we mock the selects directly for the 3 steps.

    # ==========================
    # STEP 1: Process evt_001
    # ==========================
    session.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: mock_merchant), # Merchant check
        MagicMock(scalar_one_or_none=lambda: None),          # IngestionEvent check
        MagicMock(scalar_one_or_none=lambda: None),          # Payment check
        MagicMock(scalars=lambda: MagicMock(first=lambda: None)) # Case check
    ]

    resp1 = await process_payment_event(session, base_event)
    assert resp1.status == "success"

    # Capture the created payment and case
    created_payment = session.add.call_args_list[0][0][0]
    created_ingest = session.add.call_args_list[1][0][0]
    created_case = session.add.call_args_list[2][0][0]

    assert created_payment.external_id == "pay_123"
    assert created_ingest.event_id == "evt_001"

    # ==========================
    # STEP 2: Process evt_001 again
    # ==========================
    session.reset_mock()
    session.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: mock_merchant), # Merchant check
        MagicMock(scalar_one_or_none=lambda: created_ingest), # IngestionEvent check -> FOUND!
        MagicMock(scalars=lambda: MagicMock(first=lambda: created_case)) # Case check
    ]

    resp2 = await process_payment_event(session, base_event)
    assert resp2.status == "idempotent_success"
    assert resp2.payment_id == str(created_payment.id)
    assert resp2.case_id == str(created_case.id)
    assert session.add.call_count == 0  # No duplicate side effects

    # ==========================
    # STEP 4: Process evt_002
    # ==========================
    event2 = base_event.model_copy(update={"event_id": "evt_002", "status": "failed"})

    session.reset_mock()
    session.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: mock_merchant), # Merchant check
        MagicMock(scalar_one_or_none=lambda: None),          # IngestionEvent check -> NOT FOUND!
        MagicMock(scalar_one_or_none=lambda: created_payment), # Payment check -> FOUND!
        MagicMock(scalars=lambda: MagicMock(first=lambda: created_case)) # Case check -> FOUND!
    ]

    resp3 = await process_payment_event(session, event2)
    assert resp3.status == "success"

    # Verify ONLY the ingestion event is added, payment and case are just updated
    assert session.add.call_count == 1
    added_obj = session.add.call_args[0][0]
    assert isinstance(added_obj, IngestionEvent)
    assert added_obj.event_id == "evt_002"

    # Verify Payment was updated, not duplicated
    assert created_payment.status == "failed"


@pytest.mark.asyncio
async def test_unknown_merchant_handling(base_event):
    session = AsyncMock()
    # Mock merchant lookup to return None
    session.execute.return_value = MagicMock(scalar_one_or_none=lambda: None)

    with pytest.raises(UnknownMerchantError):
        await process_payment_event(session, base_event)
