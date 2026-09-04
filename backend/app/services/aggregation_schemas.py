from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict


class ExperimentSummaryRow(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    status: str
    intervention_strategy: str
    holdout_percentage: int
    segment_filter: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    treatment_count: int
    holdout_count: int
    total_assignments: int

    model_config = ConfigDict(from_attributes=True)


class CohortMetrics(BaseModel):
    case_count: int
    amount_at_risk_minor: int
    recovered_count: int
    recovered_amount_minor: int
    recovery_rate_bps: int


class IncrementalMetrics(BaseModel):
    incremental_recovered_cases: int
    incremental_recovery_amount_minor: int
    treatment_recovery_rate_bps: int
    holdout_recovery_rate_bps: int
    lift_bps: int
    currency: str = "INR"


class InterventionBreakdownItem(BaseModel):
    intervention_type: str
    case_count: int
    recovered_count: int
    recovered_amount_minor: int
    recovery_rate_bps: int


class ExperimentDetailResult(BaseModel):
    experiment: ExperimentSummaryRow
    cohort_metrics: dict[str, CohortMetrics]
    incremental_metrics: IncrementalMetrics
    intervention_breakdown: list[InterventionBreakdownItem]
    currency: str = "INR"


class AnalyticsSummary(BaseModel):
    total_cases: int
    treatment_cases: int
    holdout_cases: int
    stopped_cases: int
    amount_at_risk_minor: int
    gross_recovered_amount_minor: int
    gross_recovery_rate_bps: int


class CohortRecoveryResult(BaseModel):
    treatment: CohortMetrics
    holdout: CohortMetrics
    incremental_recovered_cases: int
    incremental_recovery_amount_minor: int
    lift_bps: int


class InterventionPerformanceRow(BaseModel):
    intervention_type: str
    case_count: int
    recovered_count: int
    recovered_amount_minor: int
    recovery_rate_bps: int


class FailureCategoryRow(BaseModel):
    failure_category: str
    case_count: int
    amount_at_risk_minor: int
    recovered_count: int
    recovered_amount_minor: int
    recovery_rate_bps: int


class AnalyticsMetricsResponse(BaseModel):
    summary: AnalyticsSummary
    cohort_recovery: CohortRecoveryResult
    by_intervention_type: list[InterventionPerformanceRow]
    by_failure_category: list[FailureCategoryRow]
    pipeline_funnel: dict[str, int]
    currency: str = "INR"
