import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getOverviewMetrics } from '../api/overview';
import { getCases } from '../api/cases';
import { getPendingApprovals } from '../api/approvals';
import { runDemoScenario, resetDemo } from '../api/demo';
import { formatMoneyMinor, formatBps, formatTimestamp } from '../lib/formatters';
import { CaseStatusBadge } from '../components/status/CaseStatusBadge';
import { ActionStatusBadge } from '../components/status/ActionStatusBadge';
import { VerificationStatusBadge } from '../components/status/VerificationStatusBadge';
import {
  DollarSign,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  ShieldAlert,
  Loader2,
  RefreshCcw,
  Play,
  RotateCcw,
} from 'lucide-react';

export const OverviewPage: React.FC = () => {
  const queryClient = useQueryClient();

  const runMutation = useMutation({
    mutationFn: runDemoScenario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['overview-metrics'] });
      queryClient.invalidateQueries({ queryKey: ['recent-cases'] });
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
    },
  });

  const resetMutation = useMutation({
    mutationFn: resetDemo,
    onSuccess: () => {
      runMutation.reset();
      queryClient.invalidateQueries({ queryKey: ['overview-metrics'] });
      queryClient.invalidateQueries({ queryKey: ['recent-cases'] });
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
    },
  });

  const { data: metrics, isLoading: loadingMetrics, isError: errorMetrics, refetch: refetchMetrics } = useQuery({
    queryKey: ['overview-metrics'],
    queryFn: getOverviewMetrics,
  });

  const { data: casesData, isLoading: loadingCases } = useQuery({
    queryKey: ['recent-cases'],
    queryFn: () => getCases(),
  });

  const { data: approvalsData, isLoading: loadingApprovals } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: getPendingApprovals,
  });

  if (loadingMetrics || loadingCases || loadingApprovals) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
        <p className="text-sm font-mono">Loading Control Room Metrics...</p>
      </div>
    );
  }

  if (errorMetrics || !metrics) {
    return (
      <div className="p-6 rounded-lg bg-red-950/30 border border-red-800/50 text-red-300 max-w-xl">
        <div className="flex items-center gap-3 mb-2">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <h3 className="font-semibold text-sm">Failed to Load Overview Metrics</h3>
        </div>
        <p className="text-xs text-red-400 mb-4">The backend API was unreachable or returned an error.</p>
        <button
          onClick={() => refetchMetrics()}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-red-900/60 hover:bg-red-900 text-xs font-mono text-white transition"
        >
          <RefreshCcw className="w-3.5 h-3.5" /> Retry
        </button>
      </div>
    );
  }

  const kpis = [
    {
      label: 'Revenue At Risk',
      value: formatMoneyMinor(metrics.revenue_at_risk_minor, metrics.currency),
      subtext: `${metrics.total_cases} total cases tracked`,
      icon: DollarSign,
      color: 'text-amber-400',
      bgColor: 'bg-amber-950/30 border-amber-800/40',
    },
    {
      label: 'Verified Recovered Revenue',
      value: formatMoneyMinor(metrics.recovered_revenue_minor, metrics.currency),
      subtext: 'Authoritative verified funds',
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-950/30 border-emerald-800/40',
    },
    {
      label: 'Recovery Rate',
      value: formatBps(metrics.recovery_rate_bps),
      subtext: 'BPS Efficiency Score',
      icon: TrendingUp,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-950/30 border-indigo-800/40',
    },
    {
      label: 'Pending Approvals',
      value: metrics.pending_approvals,
      subtext: 'Requires Human Authorization',
      icon: Clock,
      color: metrics.pending_approvals > 0 ? 'text-amber-400' : 'text-slate-400',
      bgColor: metrics.pending_approvals > 0 ? 'bg-amber-950/40 border-amber-700/60' : 'bg-slate-900/60 border-slate-800',
    },
  ];

  const recentCases = (casesData?.items || []).slice(0, 5);
  const pendingItems = approvalsData?.items || [];
  const highestPending = pendingItems.length > 0 ? pendingItems[0] : null;

  return (
    <div className="space-y-8">
      {/* Demo Control Panel */}
      <div className="p-5 rounded-lg bg-purple-950/20 border border-purple-500/30">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Play className="w-5 h-5 text-purple-400" />
            <h2 className="text-sm font-semibold text-purple-200">Demo Mode Control Panel</h2>
          </div>
          <button
            onClick={() => resetMutation.mutate()}
            disabled={resetMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-purple-900/40 hover:bg-purple-900/60 text-purple-300 text-xs font-mono transition border border-purple-700/50 disabled:opacity-50"
          >
            {resetMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />}
            Reset Demo
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          {[
            { id: 'scenario_1', label: 'Scenario 1 (Auto Recovery)' },
            { id: 'scenario_2', label: 'Scenario 2 (Approval)' },
            { id: 'scenario_3', label: 'Scenario 3 (Stop)' },
            { id: 'scenario_4', label: 'Scenario 4 (Experiment)' },
          ].map(scenario => (
            <button
              key={scenario.id}
              onClick={() => runMutation.mutate(scenario.id)}
              disabled={runMutation.isPending}
              className="flex items-center justify-center gap-2 p-3 rounded bg-indigo-950/40 hover:bg-indigo-900/60 border border-indigo-800/50 text-indigo-300 text-xs font-semibold transition disabled:opacity-50"
            >
              {runMutation.isPending && runMutation.variables === scenario.id ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {scenario.label}
            </button>
          ))}
        </div>

        {runMutation.isSuccess && runMutation.data && (
          <div className="p-3 rounded bg-emerald-950/30 border border-emerald-800/50 flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-300 text-xs font-mono">
              <CheckCircle2 className="w-4 h-4" />
              <span>Scenario executed successfully.</span>
            </div>
            <div className="flex items-center gap-3">
              <Link to={`/cases/${runMutation.data.case_id}`} className="text-xs text-indigo-400 hover:text-indigo-300 underline font-mono">
                View Case ({runMutation.data.case_id.substring(0, 8)})
              </Link>
              {runMutation.data.action_id && (
                <Link to={`/approvals`} className="text-xs text-amber-400 hover:text-amber-300 underline font-mono">
                  View Approval
                </Link>
              )}
            </div>
          </div>
        )}

        {runMutation.isError && (
          <div className="p-3 rounded bg-red-950/30 border border-red-800/50 flex items-center gap-2 text-red-400 text-xs font-mono">
            <AlertCircle className="w-4 h-4" />
            <span>Failed to execute scenario: {runMutation.error instanceof Error ? runMutation.error.message : 'Unknown error'}</span>
          </div>
        )}
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div key={kpi.label} className={`p-4 rounded-lg border ${kpi.bgColor} flex flex-col justify-between`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{kpi.label}</span>
                <Icon className={`w-5 h-5 ${kpi.color}`} />
              </div>
              <div>
                <div className="text-2xl font-bold font-mono text-slate-100 tracking-tight">{kpi.value}</div>
                <div className="text-[11px] text-slate-400 font-mono mt-1">{kpi.subtext}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Pipeline + Approvals Attention */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Stage Distribution */}
        <div className="lg:col-span-2 p-5 rounded-lg bg-[#0c121e] border border-[#1f293d]">
          <div className="flex items-center justify-between mb-4 border-b border-[#1f293d] pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">Recovery Pipeline Lifecycle</h2>
              <p className="text-xs text-slate-400 font-mono">Case counts by state</p>
            </div>
            <Link to="/live-recovery" className="text-xs text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1">
              Live Pipeline <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Object.entries(metrics.pipeline_counts).map(([stateKey, count]) => (
              <div key={stateKey} className="p-3 rounded bg-[#111827] border border-[#1f293d]">
                <div className="text-[11px] font-mono text-slate-400 capitalize mb-1">
                  {stateKey.replace(/_/g, ' ')}
                </div>
                <div className="text-xl font-bold font-mono text-slate-100">{count}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Approval Attention Panel */}
        <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1f293d] pb-3 mb-4">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-400" />
                <h2 className="text-sm font-semibold text-slate-200">Approval Attention</h2>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                {metrics.pending_approvals} Action{metrics.pending_approvals === 1 ? '' : 's'} Pending
              </span>
            </div>

            {highestPending ? (
              <div className="p-3 rounded bg-[#111827] border border-[#1f293d] space-y-2">
                <div className="flex justify-between items-center text-xs text-slate-400 font-mono">
                  <span>Priority Case</span>
                  <span className="text-slate-300 font-semibold">{highestPending.external_payment_id}</span>
                </div>
                <div className="text-lg font-bold font-mono text-emerald-400">
                  {formatMoneyMinor(highestPending.amount_minor, highestPending.currency)}
                </div>
                <div className="text-xs text-slate-300">
                  Intervention: <span className="font-mono text-indigo-300">{highestPending.intervention_type}</span>
                </div>
                <div className="text-xs text-slate-400">
                  Expected ERV: <span className="font-mono text-emerald-400">{formatMoneyMinor(highestPending.expected_recovery_value_minor, highestPending.currency)}</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 font-mono py-4 text-center">No pending approval actions requiring attention.</p>
            )}
          </div>

          <Link
            to="/approvals"
            className="mt-4 w-full py-2 px-4 rounded bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white text-center transition flex items-center justify-center gap-2"
          >
            Go to Approval Queue <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Recent Recovery Activity */}
      <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d]">
        <div className="flex items-center justify-between border-b border-[#1f293d] pb-3 mb-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Recent Recovery Activity</h2>
            <p className="text-xs text-slate-400 font-mono">Execution != Recovery (Verified outcomes only)</p>
          </div>
          <Link to="/cases" className="text-xs text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1">
            View All Cases <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentCases.length === 0 ? (
          <p className="text-xs text-slate-400 font-mono py-6 text-center">No recovery cases found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#111827] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1f293d]">
                <tr>
                  <th className="p-3">Case ID</th>
                  <th className="p-3">Payment Reference</th>
                  <th className="p-3">Amount</th>
                  <th className="p-3">Case Status</th>
                  <th className="p-3">Action Status</th>
                  <th className="p-3">Verification</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f293d] text-slate-300">
                {recentCases.map((item) => (
                  <tr key={item.id} className="hover:bg-[#151d2d] transition">
                    <td className="p-3 font-semibold text-indigo-400">
                      <Link to={`/cases/${item.id}`} className="hover:underline">
                        {item.id.substring(0, 8)}...
                      </Link>
                    </td>
                    <td className="p-3">{item.payment?.external_id || 'â€”'}</td>
                    <td className="p-3 font-bold text-slate-100">
                      {formatMoneyMinor(item.amount_at_risk_minor, item.currency)}
                    </td>
                    <td className="p-3">
                      <CaseStatusBadge status={item.status} />
                    </td>
                    <td className="p-3">
                      {item.action ? <ActionStatusBadge status={item.action.status} /> : <span className="text-slate-500">â€”</span>}
                    </td>
                    <td className="p-3">
                      <VerificationStatusBadge status={item.verification?.status} />
                    </td>
                    <td className="p-3 text-right">
                      <Link
                        to={`/cases/${item.id}`}
                        className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300"
                      >
                        Investigate <ArrowRight className="w-3 h-3" />
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
