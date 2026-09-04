import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getPendingApprovals, approveAction, rejectAction } from '../api/approvals';
import { formatMoneyMinor, formatBps, formatTimestamp } from '../lib/formatters';
import { CheckSquare, Check, X, ArrowRight, Loader2, AlertCircle, RefreshCw } from 'lucide-react';

export const ApprovalQueuePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['pending-approvals-queue'],
    queryFn: getPendingApprovals,
  });

  const approveMut = useMutation({
    mutationFn: (actionId: string) => approveAction(actionId),
    onSuccess: (_, actionId) => {
      setFeedback({ type: 'success', message: `Action ${actionId.substring(0, 8)}... successfully approved.` });
      queryClient.invalidateQueries({ queryKey: ['pending-approvals-queue'] });
      queryClient.invalidateQueries({ queryKey: ['overview-metrics'] });
    },
    onError: (err: any) => {
      setFeedback({ type: 'error', message: err.message || 'Approval decision failed.' });
    },
  });

  const rejectMut = useMutation({
    mutationFn: (actionId: string) => rejectAction(actionId),
    onSuccess: (_, actionId) => {
      setFeedback({ type: 'success', message: `Action ${actionId.substring(0, 8)}... rejected.` });
      queryClient.invalidateQueries({ queryKey: ['pending-approvals-queue'] });
      queryClient.invalidateQueries({ queryKey: ['overview-metrics'] });
    },
    onError: (err: any) => {
      setFeedback({ type: 'error', message: err.message || 'Rejection decision failed.' });
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm font-mono">Loading Operational Approval Queue...</p>
      </div>
    );
  }

  const items = data?.items || [];

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex items-center justify-between p-4 rounded-lg bg-[#0c121e] border border-[#1f293d]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-amber-950/60 border border-amber-700/50 text-amber-400">
            <CheckSquare className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-100">Human Approval Queue</h2>
            <p className="text-xs text-slate-400 font-mono">
              High-value / high-risk interventions requiring manual authorization
            </p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#151d2d] hover:bg-[#1f293d] text-xs font-mono text-slate-300 border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Queue
        </button>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`p-4 rounded-md border text-xs font-mono flex items-center justify-between ${
            feedback.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
              : 'bg-red-950/40 border-red-800/60 text-red-300'
          }`}
        >
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Approval Queue Table */}
      <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d]">
        {items.length === 0 ? (
          <div className="text-center py-16 text-slate-400 font-mono text-xs space-y-2">
            <CheckSquare className="w-10 h-10 mx-auto text-emerald-500/40 mb-2" />
            <p className="font-semibold text-slate-300">Approval Queue Clear</p>
            <p className="text-slate-500">No actions currently require manual human authorization.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#111827] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1f293d]">
                <tr>
                  <th className="p-3">Case ID</th>
                  <th className="p-3">Payment Reference</th>
                  <th className="p-3">Amount At Risk</th>
                  <th className="p-3">Selected Intervention</th>
                  <th className="p-3">Recovery Prob</th>
                  <th className="p-3">Expected ERV</th>
                  <th className="p-3">Requested At</th>
                  <th className="p-3 text-right">Authorize</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f293d] text-slate-300">
                {items.map((item) => (
                  <tr key={item.approval_id} className="hover:bg-[#151d2d] transition">
                    <td className="p-3 font-semibold text-indigo-400">
                      <Link to={`/cases/${item.case_id}`} className="hover:underline">
                        {item.case_id.substring(0, 8)}...
                      </Link>
                    </td>
                    <td className="p-3 font-mono text-slate-300">{item.external_payment_id}</td>
                    <td className="p-3 font-bold text-slate-100">
                      {formatMoneyMinor(item.amount_minor, item.currency)}
                    </td>
                    <td className="p-3 font-bold text-indigo-300">{item.intervention_type}</td>
                    <td className="p-3 text-emerald-400">{formatBps(item.estimated_recovery_probability_bps)}</td>
                    <td className="p-3 font-bold text-emerald-400">
                      {formatMoneyMinor(item.expected_recovery_value_minor, item.currency)}
                    </td>
                    <td className="p-3 text-slate-400">{formatTimestamp(item.requested_at)}</td>
                    <td className="p-3 text-right space-x-2">
                      <button
                        onClick={() => approveMut.mutate(item.action_id)}
                        disabled={approveMut.isPending || rejectMut.isPending}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-sans text-xs font-medium transition disabled:opacity-50"
                      >
                        <Check className="w-3.5 h-3.5" /> Approve
                      </button>
                      <button
                        onClick={() => rejectMut.mutate(item.action_id)}
                        disabled={approveMut.isPending || rejectMut.isPending}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white font-sans text-xs font-medium transition disabled:opacity-50"
                      >
                        <X className="w-3.5 h-3.5" /> Reject
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
