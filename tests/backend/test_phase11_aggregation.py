import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.enums import AssignmentGroup
from app.services.experiment_aggregation import compute_experiment_detail, compute_experiment_list
from app.services.analytics_aggregation import compute_full_analytics

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session_experiment_list():
    session = AsyncMock()
    exp_mock = MagicMock()
    exp_mock.id = uuid.uuid4()
    exp_mock.name = "Test Exp"
    exp_mock.description = "Test"
    exp_mock.status.value = "active"
    exp_mock.intervention_strategy = "smart_retry"
    exp_mock.holdout_percentage = 10
    exp_mock.segment_filter = None
    exp_mock.started_at = None
    exp_mock.completed_at = None
    exp_mock.created_at = "2023-01-01"

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        if "from experiments" in stmt_str:
            result.scalars.return_value.all.return_value = [exp_mock]
        elif "experiment_assignments" in stmt_str and "count" in stmt_str:
            result.all.return_value = [(exp_mock.id, AssignmentGroup.TREATMENT, 90), (exp_mock.id, AssignmentGroup.HOLDOUT, 10)]
        return result

    session.execute.side_effect = mock_execute
    return session


@pytest.fixture
def mock_session_experiment_detail():
    session = AsyncMock()
    exp_mock = MagicMock()
    exp_mock.id = uuid.uuid4()
    exp_mock.name = "Test Exp"
    exp_mock.description = "Test"
    exp_mock.status.value = "active"
    exp_mock.intervention_strategy = "smart_retry"
    exp_mock.holdout_percentage = 10
    exp_mock.segment_filter = None
    exp_mock.started_at = None
    exp_mock.completed_at = None
    exp_mock.created_at = "2023-01-01"

    # Asymmetric setup:
    # Treatment: 90 cases, 90,000 minor risk, 45 recovered cases, 45,000 minor recovered (50%)
    # Holdout: 10 cases, 10,000 minor risk, 2 recovered cases, 2,000 minor recovered (20%)
    # Incremental cases: 45 - (90 * 20%) = 45 - 18 = 27
    # Incremental money: 45000 - (90000 * 20%) = 45000 - 18000 = 27000
    # Lift: 5000 bps - 2000 bps = 3000 bps

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()
        print("DEBUG:", stmt_str)
        print("DEBUG PARAMS:", str(stmt.compile().params.values()).lower())

        if "from experiments" in stmt_str:
            result.scalar_one_or_none.return_value = exp_mock

        elif "from cases join payments" in stmt_str and "not (exists" in stmt_str:
            result.one.return_value = (2, 2000)

        elif "from cases" in stmt_str and "count" in stmt_str and "group by" not in stmt_str:
            if "treatment" in str(stmt.compile().params.values()).lower():
                result.one.return_value = (90, 90000)
            else:
                result.one.return_value = (10, 10000)

        elif "from verifications" in stmt_str and "count" in stmt_str and "group by" not in stmt_str:
            if "treatment" in str(stmt.compile().params.values()).lower():
                result.one.return_value = (45, 45000)
            else:
                result.one.return_value = (2, 2000)

        elif "from interventions" in stmt_str and "group by" in stmt_str and "from verifications" not in stmt_str:
            # base breakdown
            result.all.return_value = [("smart_retry", 90, 90000)]

        elif "from verifications" in stmt_str and "group by" in stmt_str:
            # rec breakdown
            result.all.return_value = [("smart_retry", 45, 45000)]

        elif "from experiment_assignments" in stmt_str and "group by" not in stmt_str:
            result.scalars.return_value.all.return_value = [uuid.uuid4()]

        return result

    session.execute.side_effect = mock_execute
    return session


@pytest.fixture
def mock_session_analytics():
    session = AsyncMock()

    # Treatment: 900 cases, 900,000 minor risk, 450 recovered cases, 450,000 minor recovered (50%)
    # Holdout: 100 cases, 100,000 minor risk, 20 recovered cases, 20,000 minor recovered (20%)

    async def mock_execute(stmt):
        result = MagicMock()
        stmt_str = str(stmt).lower()

        if "from cases" in stmt_str and "count" in stmt_str and "sum" in stmt_str and "group by" not in stmt_str:
            result.one.return_value = (1000, 1000000)

        elif "from cases" in stmt_str and "sum" in stmt_str and "count" not in stmt_str:
            if "treatment" in str(stmt.compile().params.values()).lower():
                result.scalar.return_value = 900000
            else:
                result.scalar.return_value = 100000

        elif "from cases" in stmt_str and "count" in stmt_str and "sum" not in stmt_str and "group by" not in stmt_str:
            if "treatment" in str(stmt.compile().params.values()).lower():
                result.scalar.return_value = 900
            elif "holdout" in str(stmt.compile().params.values()).lower():
                result.scalar.return_value = 100
            else:
                result.scalar.return_value = 0

        elif "from verifications" in stmt_str and "sum" in stmt_str and "count" not in stmt_str:
            result.scalar.return_value = 470000

        elif "from verifications" in stmt_str and "count" in stmt_str and "group by" not in stmt_str:
            if "treatment" in str(stmt.compile().params.values()).lower():
                result.one.return_value = (450, 450000)
            else:
                result.one.return_value = (20, 20000)

        elif "from interventions" in stmt_str and "group by" in stmt_str and "verifications" not in stmt_str:
            result.all.return_value = [("smart_retry", 1000, 1000000)]

        elif "from interventions" in stmt_str and "group by" in stmt_str and "verifications" in stmt_str:
            result.all.return_value = [("smart_retry", 470, 470000)]

        elif "from cases" in stmt_str and "group by" in stmt_str and "verifications" not in stmt_str:
            # For pipeline funnel and failure category base
            if "failure_category" in stmt_str:
                result.all.return_value = [("fraud", 1000, 1000000)]
            elif "status" in stmt_str:
                result.all.return_value = [("detected", 1000)]
            else:
                result.all.return_value = []

        elif "from cases" in stmt_str and "group by" in stmt_str and "verifications" in stmt_str:
            result.all.return_value = [("fraud", 470, 470000)]

        return result

    session.execute.side_effect = mock_execute
    return session


async def test_compute_experiment_list(mock_session_experiment_list):
    results = await compute_experiment_list(mock_session_experiment_list)
    assert len(results) == 1
    assert results[0].treatment_count == 90
    assert results[0].holdout_count == 10


async def test_compute_experiment_detail(mock_session_experiment_detail):
    detail = await compute_experiment_detail(mock_session_experiment_detail, uuid.uuid4())
    assert detail is not None

    t_metrics = detail.cohort_metrics["treatment"]
    assert t_metrics.case_count == 90
    assert t_metrics.amount_at_risk_minor == 90000
    assert t_metrics.recovered_count == 45
    assert t_metrics.recovered_amount_minor == 45000
    assert t_metrics.recovery_rate_bps == 5000

    h_metrics = detail.cohort_metrics["holdout"]
    assert h_metrics.case_count == 10
    assert h_metrics.amount_at_risk_minor == 10000
    assert h_metrics.recovered_count == 2
    assert h_metrics.recovered_amount_minor == 2000
    assert h_metrics.recovery_rate_bps == 2000

    inc = detail.incremental_metrics
    assert inc.lift_bps == 3000

    # Absolute difference logic (T - H) would yield: 45000 - 2000 = 43000
    # Expected baseline logic yields: 45000 - (90000 * 0.2) = 45000 - 18000 = 27000
    # This explicitly asserts the correct formula is used!
    assert inc.incremental_recovery_amount_minor == 27000
    assert inc.incremental_recovered_cases == 27

    assert len(detail.intervention_breakdown) == 1
    assert detail.intervention_breakdown[0].intervention_type == "smart_retry"


async def test_compute_full_analytics(mock_session_analytics):
    analytics = await compute_full_analytics(mock_session_analytics)

    assert analytics.summary.total_cases == 1000
    assert analytics.summary.gross_recovered_amount_minor == 470000
    assert analytics.summary.gross_recovery_rate_bps == 4700

    # 450000 - (900000 * 2000 // 10000) = 450000 - 180000 = 270000
    assert analytics.cohort_recovery.incremental_recovery_amount_minor == 270000
    assert analytics.cohort_recovery.incremental_recovered_cases == 270
    assert analytics.cohort_recovery.lift_bps == 3000

    assert len(analytics.by_intervention_type) == 1
    assert analytics.by_intervention_type[0].intervention_type == "smart_retry"
    assert analytics.by_intervention_type[0].recovery_rate_bps == 4700

    assert len(analytics.by_failure_category) == 1
    assert analytics.by_failure_category[0].failure_category == "fraud"
    assert analytics.by_failure_category[0].recovery_rate_bps == 4700
