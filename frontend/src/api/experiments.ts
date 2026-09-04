import { fetchApi } from './client';
import type {
  ExperimentSummary,
  CohortMetrics,
  IncrementalMetrics,
  InterventionBreakdown
} from '../types';

export interface GetExperimentsResponse {
  items: ExperimentSummary[];
  total: number;
}

export interface GetExperimentResponse {
  experiment: ExperimentSummary;
  cohort_metrics: {
    treatment: CohortMetrics;
    holdout: CohortMetrics;
  };
  incremental_metrics: IncrementalMetrics;
  intervention_breakdown: InterventionBreakdown[];
}

export async function getExperiments(): Promise<GetExperimentsResponse> {
  return fetchApi<GetExperimentsResponse>('/experiments');
}

export async function getExperiment(id: string): Promise<GetExperimentResponse> {
  return fetchApi<GetExperimentResponse>(`/experiments/${id}`);
}
