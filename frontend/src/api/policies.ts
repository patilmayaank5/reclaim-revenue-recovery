import { fetchApi } from './client';
import type {
  PolicyConfig,
  EvaluationRule,
  PolicyOutcome,
  PolicyEvaluationSummary,
  RecentEvaluation
} from '../types';

export interface GetCurrentPolicyResponse {
  policy_config: PolicyConfig;
  evaluation_rules: EvaluationRule[];
  reason_codes: Record<string, string>;
  outcome_types: PolicyOutcome[];
  recent_evaluations: RecentEvaluation[];
  evaluation_summary: PolicyEvaluationSummary;
}

export async function getCurrentPolicy(): Promise<GetCurrentPolicyResponse> {
  return fetchApi<GetCurrentPolicyResponse>('/policies/current');
}
