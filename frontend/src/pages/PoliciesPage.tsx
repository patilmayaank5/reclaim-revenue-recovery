import React, { useEffect, useState } from 'react';
import { getCurrentPolicy, GetCurrentPolicyResponse } from '../api/policies';

export function PoliciesPage() {
  const [data, setData] = useState<GetCurrentPolicyResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const policyData = await getCurrentPolicy();
        setData(policyData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading || !data) {
    return <div className="p-8 text-slate-400">Loading policies...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-white">Policy Engine</h1>
          <p className="text-sm text-slate-400 mt-1">
            Current Version: v{data.policy_config.version} ”¢ Active: {data.policy_config.is_active ? 'Yes' : 'No'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Rules Chain */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Evaluation Rules Chain</h3>
          <div className="space-y-4">
            {data.evaluation_rules.map((rule, idx) => (
              <div key={rule.id} className="border border-slate-800 rounded p-4 bg-slate-800/20 relative">
                <div className="absolute top-4 right-4 flex items-center space-x-2">
                  <span className="text-xs text-slate-500 font-mono">Priority: {rule.priority}</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${
                    rule.action === 'allow_auto' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                    rule.action === 'block' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                    'bg-amber-500/10 text-amber-500 border-amber-500/20'
                  }`}>
                    {rule.action.toUpperCase()}
                  </span>
                </div>
                <h4 className="font-medium text-white mb-1">{rule.name}</h4>
                {rule.description && <p className="text-sm text-slate-400 mb-3">{rule.description}</p>}

                <div className="bg-slate-950 p-2 rounded text-xs text-slate-300 font-mono overflow-x-auto">
                  <pre>{JSON.stringify(rule.conditions, null, 2)}</pre>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Evaluations */}
        <div className="space-y-8">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Evaluation Summary</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-slate-800/30 rounded border border-slate-800">
                <div className="text-sm text-slate-400 mb-1">Total Evaluations</div>
                <div className="text-2xl font-semibold text-white">{data.evaluation_summary.total_evaluations}</div>
              </div>
              <div className="p-4 bg-slate-800/30 rounded border border-slate-800">
                <div className="text-sm text-slate-400 mb-1">Allow Auto</div>
                <div className="text-2xl font-semibold text-emerald-400">
                  {data.evaluation_summary.allow_auto_count || 0}
                </div>
              </div>
              <div className="p-4 bg-slate-800/30 rounded border border-slate-800">
                <div className="text-sm text-slate-400 mb-1">Require Approval</div>
                <div className="text-2xl font-semibold text-amber-400">
                  {data.evaluation_summary.require_approval_count || 0}
                </div>
              </div>
              <div className="p-4 bg-slate-800/30 rounded border border-slate-800">
                <div className="text-sm text-slate-400 mb-1">Blocked</div>
                <div className="text-2xl font-semibold text-red-400">
                  {data.evaluation_summary.block_count || 0}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Recent Evaluations</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-slate-500 pb-2">
                  <tr>
                    <th className="pb-3 font-medium">Time</th>
                    <th className="pb-3 font-medium">Case ID</th>
                    <th className="pb-3 font-medium">Outcome</th>
                    <th className="pb-3 font-medium">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {data.recent_evaluations.map(ev => (
                    <tr key={ev.id}>
                      <td className="py-3 text-slate-400">{new Date(ev.evaluated_at).toLocaleTimeString()}</td>
                      <td className="py-3 font-mono text-slate-300">{ev.case_id.substring(0, 8)}...</td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${
                          ev.outcome === 'allow_auto' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                          ev.outcome === 'block' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                          'bg-amber-500/10 text-amber-500 border-amber-500/20'
                        }`}>
                          {ev.outcome.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 text-slate-300" title={data.reason_codes[ev.reason_code]}>
                        {ev.reason_code}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
