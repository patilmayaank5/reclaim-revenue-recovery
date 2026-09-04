import { fetchApi } from './client';
import type {
  AnalyticsSummary,
  AnalyticsCohortRecovery,
  AnalyticsByInterventionType,
  AnalyticsByFailureCategory,
  AnalyticsPipelineFunnel
} from '../types';

export interface GetAnalyticsMetricsResponse {
  summary: AnalyticsSummary;
  cohort_recovery: AnalyticsCohortRecovery;
  by_intervention_type: AnalyticsByInterventionType[];
  by_failure_category: AnalyticsByFailureCategory[];
  pipeline_funnel: Record<string, number>;
  currency: string;
}

export async function getAnalyticsMetrics(): Promise<GetAnalyticsMetricsResponse> {
  return fetchApi<GetAnalyticsMetricsResponse>('/analytics/metrics');
}
