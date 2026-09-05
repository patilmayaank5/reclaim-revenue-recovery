import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCaseInvestigation, diagnoseCase, generateInterventions, evaluatePolicy, createAction } from '../api/cases';
import { executeAction, verifyAction } from '../api/actions';
import { approveAction, rejectAction } from '../api/approvals';
import { formatMoneyMinor, formatBps, formatConfidence, formatTimestamp } from '../lib/formatters';
import { CaseStatusBadge } from '../components/status/CaseStatusBadge';
import { ActionStatusBadge } from '../components/status/ActionStatusBadge';
import { VerificationStatusBadge } from '../components/status/VerificationStatusBadge';
import { AssignmentBadge } from '../components/status/AssignmentBadge';
import {
  CreditCard,
  Brain,
  Layers,
  Shield,
  Zap,
  CheckCircle,
  ArrowLeft,
  Loader2,
  AlertTriangle,
  Play,
  Check,
  X,
  SearchCheck,
} from 'lucide-react';

export const CaseInvestigationPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['case-investigation', caseId],
    queryFn: () => getCaseInvestigation(caseId!),
    enabled: !!caseId,
  });

  // Pipeline execution mutations
  const diagnoseMutation = useMutation({
    mutationFn: () => diagnoseCase(caseId!),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['case-investigation', caseId] });
    },
    onError: (err: any) => setActionError(err.message),
  });

  const interventionsMutation = useMutation({
    mutationFn: () => generateInterventions(caseId!),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['case-investigation', caseId] });
    },
    onError: (err: any) => setActionError(err.message),
  });

  const policyMutation = useMutation({
    mutationFn: () => evaluatePolicy(caseId!),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['case-investigation', caseId] });
    },
    onError: (err: any) => setActionError(err.message),
  });

  const createActionMutation = useMutation({
    mutationFn: () => createAction(caseId!),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['case-investigation', caseId] });
    },
    onError: (err: any) => setActionError(err.message),
  });

  const executeMutation = useMutation({
    mutationFn: (actionId: string) => executeAction(actionId),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['case-investigation', caseId] });
    },
    onError: (err: any) => setActionError(err.message),
  });

  const verifyMutation = useMutation({
    mutationFn: ({ actionId, scenario }: { actionId: string; scenario?: string }) => verifyAction(actionId, scenario),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['case-investigation', caseId] });
    },
    onError: (err: any) => setActionError(err.message),
  });

  const approveMutation = useMutation({
    mutationFn: (actionId: string) => approveAction(actionId),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['case-investigation', caseId] });
    },
    onError: (err: any) => setActionError(err.message),
  });

  const rejectMutation = useMutation({
    mutationFn: (actionId: string) => rejectAction(actionId),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['case-investigation', caseId] });
    },
    onError: (err: any) => setActionError(err.message),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm font-mono">Loading Case Investigation Surface...</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-6 rounded-lg bg-red-950/30 border border-red-800/50 text-red-300 max-w-xl">
        <h3 className="font-semibold text-sm mb-2">Case Investigation Not Found</h3>
        <p className="text-xs text-red-400 mb-4">Unable to fetch case record from backend API.</p>
        <Link to="/cases" className="inline-flex items-center gap-2 text-xs font-mono text-indigo-400">
          <ArrowLeft className="w-4 h-4" /> Back to Cases
        </Link>
      </div>
    );
  }

  const { case: c, payment: pay, diagnosis: diag, interventions, action: act, verification: verif } = data;
  const isExecutingAny =
    diagnoseMutation.isPending ||
    interventionsMutation.isPending ||
    policyMutation.isPending ||
    createActionMutation.isPending ||
    executeMutation.isPending ||
    verifyMutation.isPending ||
    approveMutation.isPending ||
    rejectMutation.isPending;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link to="/cases" className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200">
          <ArrowLeft className="w-4 h-4" /> Return to Cases Table
        </Link>
        <span className="text-xs font-mono text-slate-500">Case Investigation ID: {c.id}</span>
      </div>

      {/* Action Error Alert */}
      {actionError && (
        <div className="p-4 rounded-md bg-red-950/40 border border-red-800/60 text-red-300 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>Workflow Error: {actionError}</span>
          </div>
          <button onClick={() => setActionError(null)} className="text-xs text-red-400 hover:underline font-mono">
            Dismiss
          </button>
        </div>
      )}

      {/* HEADER SECTION */}
      <div className="p-6 rounded-lg bg-[#0c121e] border border-[#1f293d] space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1f293d] pb-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-lg font-bold font-mono text-slate-100">Case #{c.id.substring(0, 13)}</h1>
              <CaseStatusBadge status={c.status} />
              <AssignmentBadge group={c.assignment_group} />
            </div>
            <p className="text-xs font-mono text-slate-400">Payment Reference: {pay?.external_id || '—'}</p>
          </div>
          <div className="text-left md:text-right">
            <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">Amount At Risk</div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {formatMoneyMinor(c.amount_at_risk_minor, c.currency)}
            </div>
          </div>
        </div>

        {/* Operational Workflow Controls */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs font-mono text-slate-500 mr-2">Lifecycle Controls:</span>
          {!diag && (
            <button
              onClick={() => diagnoseMutation.mutate()}
              disabled={isExecutingAny}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition disabled:opacity-50"
            >
              {diagnoseMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Brain className="w-3.5 h-3.5" />}
              Diagnose Failure
            </button>
          )}

          {diag && (!interventions || interventions.length === 0) && (
            <button
              onClick={() => interventionsMutation.mutate()}
              disabled={isExecutingAny}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition disabled:opacity-50"
            >
              {interventionsMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Layers className="w-3.5 h-3.5" />}
              Plan Interventions
            </button>
          )}

          {interventions && interventions.length > 0 && !act && (
            <>
              <button
                onClick={() => policyMutation.mutate()}
                disabled={isExecutingAny}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition disabled:opacity-50"
              >
                {policyMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Shield className="w-3.5 h-3.5" />}
                Evaluate Policy
              </button>
              <button
                onClick={() => createActionMutation.mutate()}
                disabled={isExecutingAny}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white transition disabled:opacity-50"
              >
                {createActionMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                Create Action Record
              </button>
            </>
          )}

          {act && act.status === 'pending_approval' && (
            <>
              <button
                onClick={() => approveMutation.mutate(act.id)}
                disabled={isExecutingAny}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white transition disabled:opacity-50"
              >
                {approveMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                Approve Action
              </button>
              <button
                onClick={() => rejectMutation.mutate(act.id)}
                disabled={isExecutingAny}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-xs font-semibold text-white transition disabled:opacity-50"
              >
                {rejectMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <X className="w-3.5 h-3.5" />}
                Reject Action
              </button>
            </>
          )}

          {act && (act.status === 'approved' || act.status === 'planned') && (
            <button
              onClick={() => executeMutation.mutate(act.id)}
              disabled={isExecutingAny}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white transition disabled:opacity-50"
            >
              {executeMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Execute Intervention
            </button>
          )}

          {act && (act.status === 'executed' || act.status === 'executing') && (!verif || verif.status === 'pending') && (
            <button
              onClick={() => verifyMutation.mutate({ actionId: act.id, scenario: 'recovered' })}
              disabled={isExecutingAny}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-teal-600 hover:bg-teal-500 text-xs font-semibold text-white transition disabled:opacity-50"
            >
              {verifyMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <SearchCheck className="w-3.5 h-3.5" />}
              Verify Payment Recovery
            </button>
          )}
        </div>
      </div>

      {/* 6-SECTION INVESTIGATION HIERARCHY */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SECTION 1: PAYMENT / FAILURE CONTEXT */}
        <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d] space-y-3">
          <div className="flex items-center gap-2 border-b border-[#1f293d] pb-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
            <CreditCard className="w-4 h-4 text-indigo-400" />
            <span>Section 1 — Payment / Failure Context</span>
          </div>
          {pay ? (
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div>
                <span className="text-slate-500 block">External Ref</span>
                <span className="text-slate-200 font-semibold">{pay.external_id}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Payment Method</span>
                <span className="text-slate-200">{pay.payment_method || '—'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Failure Code</span>
                <span className="text-rose-400 font-semibold">{pay.failure_code || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Provider</span>
                <span className="text-slate-200">{pay.provider}</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-500 block">Failure Description</span>
                <span className="text-slate-300">{pay.failure_description || 'No detailed description.'}</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 font-mono">Payment context not loaded.</p>
          )}
        </div>

        {/* SECTION 2: AI DIAGNOSIS */}
        <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d] space-y-3">
          <div className="flex items-center gap-2 border-b border-[#1f293d] pb-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
            <Brain className="w-4 h-4 text-indigo-400" />
            <span>Section 2 — AI Diagnosis</span>
          </div>
          {diag ? (
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Diagnosis Category</span>
                <span className="text-indigo-300 font-semibold">{diag.category}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Raw AI Confidence</span>
                <span className="text-slate-200">{formatConfidence(diag.ai_confidence)}</span>
              </div>
              <div className="flex justify-between items-center border-t border-[#1f293d] pt-2">
                <span className="text-slate-500">Calibrated Recovery Probability</span>
                <span className="text-emerald-400 font-bold">
                  {diag.recovery_probability != null ? formatConfidence(diag.recovery_probability) : 'Calculated in Phase 5'}
                </span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 font-mono py-4">Diagnosis pending. Click "Diagnose Failure" above.</div>
          )}
        </div>

        {/* SECTION 3: INTERVENTION CANDIDATES */}
        <div className="md:col-span-2 p-5 rounded-lg bg-[#0c121e] border border-[#1f293d] space-y-3">
          <div className="flex items-center gap-2 border-b border-[#1f293d] pb-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Section 3 — Intervention Candidates (Ranked by ERV)</span>
          </div>
          {!interventions || interventions.length === 0 ? (
            <p className="text-xs text-slate-500 font-mono py-4">No intervention candidates generated yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#111827] text-slate-400 uppercase text-[10px] border-b border-[#1f293d]">
                  <tr>
                    <th className="p-2">Rank</th>
                    <th className="p-2">Intervention</th>
                    <th className="p-2">Recovery Prob</th>
                    <th className="p-2">Cost</th>
                    <th className="p-2">Risk Penalty</th>
                    <th className="p-2">Expected Recovery Value (ERV)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1f293d]">
                  {interventions.map((inv) => (
                    <tr key={inv.id} className={inv.rank === 1 ? 'bg-indigo-950/20 font-medium' : ''}>
                      <td className="p-2 text-slate-400">#{inv.rank}</td>
                      <td className="p-2 text-indigo-300 font-bold">{inv.intervention_type}</td>
                      <td className="p-2 text-emerald-400">{formatBps(inv.estimated_recovery_probability_bps)}</td>
                      <td className="p-2 text-slate-300">{formatMoneyMinor(inv.intervention_cost_minor, inv.currency)}</td>
                      <td className="p-2 text-rose-300">{formatMoneyMinor(inv.risk_penalty_minor, inv.currency)}</td>
                      <td className="p-2 text-emerald-400 font-bold">
                        {formatMoneyMinor(inv.expected_recovery_value_minor, inv.currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* SECTION 4: POLICY DECISION & SECTION 5: ACTION */}
        <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d] space-y-3">
          <div className="flex items-center gap-2 border-b border-[#1f293d] pb-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
            <Shield className="w-4 h-4 text-indigo-400" />
            <span>Section 4 — Policy Authorization</span>
          </div>
          {act ? (
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Action Status</span>
                <ActionStatusBadge status={act.status} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Idempotency Key</span>
                <span className="text-slate-300 text-[11px] truncate max-w-[200px]">{act.idempotency_key}</span>
              </div>
              {act.approval && (
                <div className="mt-2 p-2.5 rounded bg-[#111827] border border-[#1f293d] space-y-1">
                  <div className="text-[11px] text-amber-400 font-semibold">Human Approval Record</div>
                  <div className="text-slate-300 text-[11px]">Status: {act.approval.status}</div>
                  {act.approval.decision_reason && (
                    <div className="text-slate-400 text-[10px]">Reason: {act.approval.decision_reason}</div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-500 font-mono py-4">Action record not created yet.</p>
          )}
        </div>

        {/* SECTION 6: VERIFICATION */}
        <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d] space-y-3">
          <div className="flex items-center gap-2 border-b border-[#1f293d] pb-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
            <CheckCircle className="w-4 h-4 text-indigo-400" />
            <span>Section 6 — Verification (Authoritative Recovery)</span>
          </div>
          {verif ? (
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Verification Outcome</span>
                <VerificationStatusBadge status={verif.status} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Observed Payment Status</span>
                <span className="text-slate-200">{verif.observed_payment_status || '—'}</span>
              </div>
              <div className="flex justify-between items-center border-t border-[#1f293d] pt-2">
                <span className="text-slate-500">Verified Recovered Amount</span>
                <span className="text-emerald-400 font-bold">{formatMoneyMinor(verif.recovered_amount_minor, c.currency)}</span>
              </div>
              <div className="text-[10px] text-slate-500">Verified at: {formatTimestamp(verif.verified_at)}</div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 font-mono py-4">
              {act?.status === 'executed' ? 'Executed! Verification pending.' : 'Verification strictly occurs post-execution.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
