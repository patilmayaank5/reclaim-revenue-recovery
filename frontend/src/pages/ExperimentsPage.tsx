import React, { useEffect, useState } from 'react';
import { getExperiments, getExperiment, GetExperimentResponse } from '../api/experiments';
import { ExperimentSummary } from '../types';
import { ExperimentStatusBadge } from '../components/status/ExperimentStatusBadge';
import { MetricCard } from '../components/shared/MetricCard';
import { formatMoneyMinor, formatBps } from '../lib/formatters';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export function ExperimentsPage() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<GetExperimentResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getExperiments();
        setExperiments(data.items);
        if (data.items.length > 0) {
          const detail = await getExperiment(data.items[0].id);
          setSelectedExperiment(detail);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  async function handleSelect(id: string) {
    try {
      const detail = await getExperiment(id);
      setSelectedExperiment(detail);
    } catch (err) {
      console.error(err);
    }
  }

  if (loading) {
    return <div className="p-8 text-slate-400">Loading experiments...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-white">A/B Experiments</h1>
          <p className="text-sm text-slate-400 mt-1">Manage and analyze recovery strategies</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-lg font-medium text-white mb-4">Active Experiments</h2>
          <div className="space-y-2">
            {experiments.map(exp => (
              <button
                key={exp.id}
                onClick={() => handleSelect(exp.id)}
                className={`w-full text-left p-4 rounded-lg border transition-colors ${
                  selectedExperiment?.experiment.id === exp.id
                    ? 'bg-slate-800 border-indigo-500/50'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium text-white">{exp.name}</span>
                  <ExperimentStatusBadge status={exp.status} />
                </div>
                <div className="text-xs text-slate-400">
                  Holdout: {exp.holdout_percentage}%
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        {selectedExperiment && (
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
              <h2 className="text-xl font-medium text-white mb-2">{selectedExperiment.experiment.name}</h2>
              <p className="text-slate-400 text-sm mb-6">{selectedExperiment.experiment.description || 'No description provided.'}</p>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <MetricCard
                  title="Treatment Recovery"
                  value={formatBps(selectedExperiment.cohort_metrics.treatment.recovery_rate_bps)}
                  subtitle={`${selectedExperiment.cohort_metrics.treatment.recovered_count} / ${selectedExperiment.cohort_metrics.treatment.case_count} cases`}
                />
                <MetricCard
                  title="Holdout Recovery"
                  value={formatBps(selectedExperiment.cohort_metrics.holdout.recovery_rate_bps)}
                  subtitle={`${selectedExperiment.cohort_metrics.holdout.recovered_count} / ${selectedExperiment.cohort_metrics.holdout.case_count} cases`}
                />
                <MetricCard
                  title="Incremental Lift"
                  value={formatBps(selectedExperiment.incremental_metrics.lift_bps)}
                  subtitle={`${selectedExperiment.incremental_metrics.incremental_recovered_cases} Incremental Cases`}
                  className="border-indigo-500/20 bg-indigo-500/5"
                />
                <MetricCard
                  title="Incremental Value"
                  value={formatMoneyMinor(selectedExperiment.incremental_metrics.incremental_recovery_amount_minor, selectedExperiment.incremental_metrics.currency)}
                  className="border-green-500/20 bg-green-500/5"
                />
              </div>

              <h3 className="text-lg font-medium text-white mb-4">Treatment Intervention Performance</h3>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={selectedExperiment.intervention_breakdown} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="intervention_type" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(v) => `${(v / 100).toFixed(1)}%`} />
                    <RechartsTooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                      itemStyle={{ color: '#e2e8f0' }}
                      formatter={(value: number) => [formatBps(value), 'Recovery Rate']}
                    />
                    <Legend />
                    <Bar dataKey="recovery_rate_bps" name="Treatment" fill="#818cf8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
