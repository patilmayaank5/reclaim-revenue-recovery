// Reclaim Control Room — Domain Types

export type CaseStatus =
  | 'detected'
  | 'enriched'
  | 'diagnosed'
  | 'intervention_planned'
  | 'action_pending'
  | 'action_approved'
  | 'action_executing'
  | 'action_executed'
  | 'verifying'
  | 'recovered'
  | 'not_recovered'
  | 'closed'
  | 'stopped';

export type ActionStatus =
  | 'planned'
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'executing'
  | 'executed'
  | 'failed';

export type VerificationStatus =
  | 'pending'
  | 'verified_recovered'
  | 'verified_not_recovered'
  | 'verification_failed'
  | 'inconclusive';

export type PaymentStatus =
  | 'pending'
  | 'authorized'
  | 'captured'
  | 'failed'
  | 'refunded';

export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export type AssignmentGroup = 'treatment' | 'holdout';

export type PolicyOutcome = 'allow_auto' | 'require_approval' | 'block';

export interface PaymentSummary {
  id?: string;
  external_id: string;
  amount_minor: number;
  currency: string;
  status: PaymentStatus;
  payment_method?: string | null;
  provider?: string;
  failure_code?: string | null;
  failure_description?: string | null;
  attempted_at?: string | null;
}

export interface AIDiagnosisSummary {
  id?: string;
  category: string;
  ai_confidence: number; // Raw AI confidence (0-1)
  recovery_probability?: number | null; // Calibrated recovery probability
  evidence?: Record<string, any> | null;
  model_provider?: string;
  model_name?: string;
}

export interface InterventionCandidate {
  id: string;
  intervention_type: string;
  recoverable_amount_minor: number;
  currency: string;
  estimated_recovery_probability_bps: number;
  intervention_cost_minor: number;
  risk_penalty_minor: number;
  expected_recovery_value_minor: number;
  rank: number;
  rationale?: string | null;
}

export interface ActionSummary {
  id: string;
  intervention_id?: string;
  status: ActionStatus;
  provider: string;
  idempotency_key: string;
  execution_metadata?: Record<string, any> | null;
  executed_at?: string | null;
  approval?: ApprovalSummary | null;
}

export interface ApprovalSummary {
  id: string;
  status: ApprovalStatus;
  requested_at?: string | null;
  decided_at?: string | null;
  approver_id?: string | null;
  decision_reason?: string | null;
}

export interface VerificationSummary {
  id?: string;
  status: VerificationStatus;
  observed_payment_status?: string | null;
  recovered_amount_minor?: number | null;
  currency?: string | null;
  provider_event_id?: string | null;
  verified_at?: string | null;
}

export interface CaseItem {
  id: string;
  payment_id: string;
  merchant_id: string;
  status: CaseStatus;
  assignment_group?: AssignmentGroup | null;
  amount_at_risk_minor: number;
  currency: string;
  failure_category?: string | null;
  detected_at?: string | null;
  resolved_at?: string | null;
  payment?: PaymentSummary | null;
  diagnosis?: AIDiagnosisSummary | null;
  action?: ActionSummary | null;
  verification?: VerificationSummary | null;
}

export interface CaseInvestigationDetail {
  case: CaseItem;
  payment?: PaymentSummary | null;
  diagnosis?: AIDiagnosisSummary | null;
  interventions: InterventionCandidate[];
  action?: ActionSummary | null;
  verification?: VerificationSummary | null;
}

export interface PendingApprovalItem {
  approval_id: string;
  action_id: string;
  case_id: string;
  payment_id: string;
  external_payment_id: string;
  amount_minor: number;
  currency: string;
  intervention_type: string;
  expected_recovery_value_minor: number;
  estimated_recovery_probability_bps: number;
  requested_at?: string | null;
  status: ApprovalStatus;
}

export interface OverviewMetrics {
  revenue_at_risk_minor: number;
  recovered_revenue_minor: number;
  recovery_rate_bps: number;
  total_cases: number;
  pending_approvals: number;
  pipeline_counts: Record<string, number>;
  currency: string;
}

// Phase 11 Types

export interface ExperimentSummary {
  id: string;
  name: string;
  description?: string;
  status: string;
  intervention_strategy: string;
  holdout_percentage: number;
  segment_filter?: any;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  treatment_count: number;
  holdout_count: number;
  total_assignments: number;
}

export interface CohortMetrics {
  case_count: number;
  amount_at_risk_minor: number;
  recovered_count: number;
  recovered_amount_minor: number;
  recovery_rate_bps: number;
}

export interface IncrementalMetrics {
  incremental_recovered_cases: number;
  incremental_recovery_amount_minor: number;
  treatment_recovery_rate_bps: number;
  holdout_recovery_rate_bps: number;
  lift_bps: number;
  currency: string;
}

export interface InterventionBreakdown {
  intervention_type: string;
  case_count: number;
  recovered_count: number;
  recovered_amount_minor: number;
  recovery_rate_bps: number;
}

export interface AnalyticsSummary {
  total_cases: number;
  treatment_cases: number;
  holdout_cases: number;
  stopped_cases: number;
  amount_at_risk_minor: number;
  gross_recovered_amount_minor: number;
  gross_recovery_rate_bps: number;
}

export interface AnalyticsCohortRecovery {
  treatment: CohortMetrics;
  holdout: CohortMetrics;
  incremental_recovered_cases: number;
  incremental_recovery_amount_minor: number;
  lift_bps: number;
}

export interface AnalyticsByInterventionType {
  intervention_type: string;
  case_count: number;
  recovered_count: number;
  recovered_amount_minor: number;
  recovery_rate_bps: number;
}

export interface AnalyticsByFailureCategory {
  failure_category: string;
  case_count: number;
  amount_at_risk_minor: number;
  recovered_count: number;
  recovered_amount_minor: number;
  recovery_rate_bps: number;
}

export interface AnalyticsPipelineFunnel {
  [stage: string]: number;
}

export interface PolicyConfig {
  id: string;
  name: string;
  is_active: boolean;
  version: number;
  created_at: string;
}

export interface EvaluationRule {
  id: string;
  name: string;
  description?: string;
  priority: number;
  conditions: any;
  action: PolicyOutcome;
}

export interface PolicyEvaluationSummary {
  total_evaluations: number;
  allow_auto_count: number;
  require_approval_count: number;
  block_count: number;
}

export interface RecentEvaluation {
  id: string;
  case_id: string;
  evaluated_at: string;
  outcome: PolicyOutcome;
  reason_code: string;
}

export interface AuditEventItem {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor: string;
  timestamp: string;
  event_data: any;
}
