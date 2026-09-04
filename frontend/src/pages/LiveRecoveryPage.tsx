import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getCases } from '../api/cases';
import { formatMoneyMinor, formatTimestamp } from '../lib/formatters';
import { CaseStatusBadge } from '../components/status/CaseStatusBadge';
import { ActionStatusBadge } from '../components/status/ActionStatusBadge';
import { VerificationStatusBadge } from '../components/status/VerificationStatusBadge';
import { Activity, ArrowRight, Loader2, RefreshCw } from 'lucide-react';

export const LiveRecoveryPage: React.FC = () => {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['live-cases'],
    queryFn: () => getCases(),
    refetchInterval: 5000, // Poll every 5s for live operational feel
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm font-mono">Connecting to Live Recovery Stream...</p>
      </div>
    );
  }

  const cases = data?.items || [];

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex items-center justify-between p-4 rounded-lg bg-[#0c121e] border border-[#1f293d]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-indigo-950/60 border border-indigo-700/50 text-indigo-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-100">Live Recovery Pipeline Monitor</h2>
            <p className="text-xs text-slate-400 font-mono">
              Deterministic state machine tracking (Auto-refreshes every 5s)
            </p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#151d2d] hover:bg-[#1f293d] text-xs font-mono text-slate-300 border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Stream
        </button>
      </div>

      {/* Live Operational Table */}
      <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d]">
        {cases.length === 0 ? (
          <div className="text-center py-12 text-slate-400 font-mono text-xs">
            No live recovery cases currently in pipeline.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#111827] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1f293d]">
                <tr>
                  <th className="p-3">Case</th>
                  <th className="p-3">Payment</th>
                  <th className="p-3">Amount</th>
                  <th className="p-3">Failure Category</th>
                  <th className="p-3">AI Diagnosis</th>
                  <th className="p-3">Current Lifecycle State</th>
                  <th className="p-3">Action State</th>
                  <th className="p-3">Verification Outcome</th>
                  <th className="p-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f293d] text-slate-300">
                {cases.map((c) => (
                  <tr key={c.id} className="hover:bg-[#151d2d] transition">
                    <td className="p-3 font-semibold text-indigo-400">
                      <Link to={`/cases/${c.id}`} className="hover:underline">
                        {c.id.substring(0, 8)}...
                      </Link>
                    </td>
                    <td className="p-3 font-mono text-slate-300">{c.payment?.external_id || 'â€”'}</td>
                    <td className="p-3 font-bold text-slate-100">
                      {formatMoneyMinor(c.amount_at_risk_minor, c.currency)}
                    </td>
                    <td className="p-3 text-slate-400">{c.failure_category || 'Unclassified'}</td>
                    <td className="p-3 text-indigo-300">{c.diagnosis?.category || 'Pending'}</td>
                    <td className="p-3">
                      <CaseStatusBadge status={c.status} />
                    </td>
                    <td className="p-3">
                      {c.action ? <ActionStatusBadge status={c.action.status} /> : <span className="text-slate-500">â€”</span>}
                    </td>
                    <td className="p-3">
                      <VerificationStatusBadge status={c.verification?.status} />
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        to={`/cases/${c.id}`}
                        className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 font-sans font-medium"
                      >
                        Investigate <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
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
