import React from 'react';

interface ExperimentStatusBadgeProps {
  status: string;
  className?: string;
}

export function ExperimentStatusBadge({ status, className = '' }: ExperimentStatusBadgeProps) {
  const styles: Record<string, string> = {
    running: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    completed: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    paused: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    draft: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${styles[status] || styles.draft} ${className}`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
