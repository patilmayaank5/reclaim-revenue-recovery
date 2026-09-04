import React from 'react';
import { ActionStatus } from '../../types';

interface Props {
  status: ActionStatus | string;
}

export const ActionStatusBadge: React.FC<Props> = ({ status }) => {
  const normalized = status.toLowerCase();

  const styleMap: Record<string, { bg: string; text: string; border: string; label: string }> = {
    planned: { bg: 'bg-slate-800/60', text: 'text-slate-300', border: 'border-slate-700', label: 'Planned' },
    pending_approval: { bg: 'bg-amber-950/50', text: 'text-amber-300', border: 'border-amber-700/60', label: 'Pending Approval' },
    approved: { bg: 'bg-emerald-950/40', text: 'text-emerald-300', border: 'border-emerald-800/50', label: 'Approved' },
    rejected: { bg: 'bg-rose-950/50', text: 'text-rose-300', border: 'border-rose-800/50', label: 'Rejected' },
    executing: { bg: 'bg-sky-950/60', text: 'text-sky-300', border: 'border-sky-700/70', label: 'Executing' },
    executed: { bg: 'bg-cyan-950/50', text: 'text-cyan-300', border: 'border-cyan-700/60', label: 'Executed' },
    failed: { bg: 'bg-red-950/50', text: 'text-red-300', border: 'border-red-800/50', label: 'Failed' },
  };

  const current = styleMap[normalized] || {
    bg: 'bg-slate-900',
    text: 'text-slate-300',
    border: 'border-slate-800',
    label: status.replace(/_/g, ' '),
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border ${current.bg} ${current.text} ${current.border}`}
      aria-label={`Action status: ${current.label}`}
    >
      {current.label}
    </span>
  );
};
