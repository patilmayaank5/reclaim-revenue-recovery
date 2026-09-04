import React from 'react';
import { CaseStatus } from '../../types';

interface Props {
  status: CaseStatus | string;
}

export const CaseStatusBadge: React.FC<Props> = ({ status }) => {
  const normalized = status.toLowerCase();

  const styleMap: Record<string, { bg: string; text: string; border: string; label: string }> = {
    detected: { bg: 'bg-slate-800/60', text: 'text-slate-300', border: 'border-slate-700', label: 'Detected' },
    enriched: { bg: 'bg-indigo-950/40', text: 'text-indigo-300', border: 'border-indigo-800/50', label: 'Enriched' },
    diagnosed: { bg: 'bg-blue-950/40', text: 'text-blue-300', border: 'border-blue-800/50', label: 'Diagnosed' },
    intervention_planned: { bg: 'bg-purple-950/40', text: 'text-purple-300', border: 'border-purple-800/50', label: 'Intervention Planned' },
    action_pending: { bg: 'bg-amber-950/40', text: 'text-amber-300', border: 'border-amber-800/50', label: 'Action Pending' },
    action_approved: { bg: 'bg-cyan-950/40', text: 'text-cyan-300', border: 'border-cyan-800/50', label: 'Action Approved' },
    action_executing: { bg: 'bg-sky-950/50', text: 'text-sky-300', border: 'border-sky-700/60', label: 'Executing' },
    action_executed: { bg: 'bg-teal-950/40', text: 'text-teal-300', border: 'border-teal-800/50', label: 'Executed' },
    verifying: { bg: 'bg-yellow-950/50', text: 'text-yellow-300', border: 'border-yellow-700/60', label: 'Verifying' },
    recovered: { bg: 'bg-emerald-950/60', text: 'text-emerald-300', border: 'border-emerald-700/60', label: 'Verified Recovered' },
    not_recovered: { bg: 'bg-rose-950/50', text: 'text-rose-300', border: 'border-rose-800/50', label: 'Not Recovered' },
    stopped: { bg: 'bg-gray-900', text: 'text-gray-400', border: 'border-gray-800', label: 'Stopped' },
    closed: { bg: 'bg-gray-900', text: 'text-gray-400', border: 'border-gray-800', label: 'Closed' },
  };

  const current = styleMap[normalized] || {
    bg: 'bg-slate-900',
    text: 'text-slate-300',
    border: 'border-slate-800',
    label: status.replace(/_/g, ' '),
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium border ${current.bg} ${current.text} ${current.border}`}
      aria-label={`Case status: ${current.label}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-80" />
      {current.label}
    </span>
  );
};
