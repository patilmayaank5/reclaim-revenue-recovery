import React, { useEffect, useState } from 'react';
import { getAnalyticsMetrics, GetAnalyticsMetricsResponse } from '../api/analytics';
import { MetricCard } from '../components/shared/MetricCard';
import { formatMoneyMinor, formatBps } from '../lib/formatters';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

export function AnalyticsPage() {
  const [data, setData] = useState<GetAnalyticsMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const metrics = await getAnalyticsMetrics();
        setData(metrics);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading || !data) {
    return <div className="p-8 text-slate-400">Loading analytics...</div>;
  }

  const pipelineData = Object.entries(data.pipeline_funnel).map(([stage, count]) => ({
    stage,
    count
  }));

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-white">Analytics Overview</h1>
        <p className="text-sm text-slate-400 mt-1">Platform performance and recovery metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Revenue at Risk"
          value={formatMoneyMinor(data.summary.amount_at_risk_minor, data.currency)}
          subtitle={`${data.summary.total_cases.toLocaleString()} total cases`}
        />
        <MetricCard
          title="Gross Recovered Revenue"
          value={formatMoneyMinor(data.summary.gross_recovered_amount_minor, data.currency)}
          className="border-emerald-500/20"
        />
        <MetricCard
          title="Overall Recovery Rate"
          value={formatBps(data.summary.gross_recovery_rate_bps)}
          trend={{ value: 'Target: 65%', isPositive: data.summary.gross_recovery_rate_bps >= 6500 }}
        />
        <MetricCard
          title="Avg Recovery Value"
          value={formatMoneyMinor(
            Math.round(data.summary.gross_recovered_amount_minor / (data.summary.total_cases || 1)),
            data.currency
          )}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Overall Cohort Recovery</h3>
          <div className="space-y-4">
             <MetricCard
              title="Incremental Value"
              value={formatMoneyMinor(data.cohort_recovery.incremental_recovery_amount_minor, data.currency)}
              subtitle={`${data.cohort_recovery.incremental_recovered_cases} Incremental Cases`}
              className="border-indigo-500/20 bg-indigo-500/5"
            />
             <MetricCard
              title="Overall Lift"
              value={formatBps(data.cohort_recovery.lift_bps)}
              className="border-slate-700 bg-slate-800"
            />
             <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="p-4 bg-slate-800 rounded border border-slate-700">
                  <div className="text-sm text-slate-400">Treatment Recovery</div>
                  <div className="text-lg text-white font-medium">{formatBps(data.cohort_recovery.treatment.recovery_rate_bps)}</div>
                </div>
                <div className="p-4 bg-slate-800 rounded border border-slate-700">
                  <div className="text-sm text-slate-400">Holdout Recovery</div>
                  <div className="text-lg text-white font-medium">{formatBps(data.cohort_recovery.holdout.recovery_rate_bps)}</div>
                </div>
             </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Pipeline Funnel</h3>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipelineData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" fontSize={12} />
                <YAxis dataKey="stage" type="category" stroke="#94a3b8" fontSize={12} width={100} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800">
          <h3 className="text-lg font-medium text-white">Intervention Performance</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/50 text-slate-400">
              <tr>
                <th className="px-6 py-3 font-medium">Intervention Type</th>
                <th className="px-6 py-3 font-medium text-right">Case Count</th>
                <th className="px-6 py-3 font-medium text-right">Recovery Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-slate-300">
              {data.by_intervention_type.map((item, i) => (
                <tr key={i} className="hover:bg-slate-800/20">
                  <td className="px-6 py-4">{item.intervention_type}</td>
                  <td className="px-6 py-4 text-right">{item.case_count.toLocaleString()}</td>
                  <td className="px-6 py-4 text-right font-medium text-white">{formatBps(item.recovery_rate_bps)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
