import React from 'react';

interface AuditEventTypeBadgeProps {
  eventType: string;
  className?: string;
}

export function AuditEventTypeBadge({ eventType, className = '' }: AuditEventTypeBadgeProps) {
  let colorClass = 'bg-slate-500/10 text-slate-400 border-slate-500/20';

  if (eventType.includes('create')) {
    colorClass = 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
  } else if (eventType.includes('update') || eventType.includes('modify')) {
    colorClass = 'bg-blue-500/10 text-blue-500 border-blue-500/20';
  } else if (eventType.includes('delete') || eventType.includes('remove')) {
    colorClass = 'bg-red-500/10 text-red-500 border-red-500/20';
  } else if (eventType.includes('fail') || eventType.includes('error')) {
    colorClass = 'bg-red-500/10 text-red-500 border-red-500/20';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colorClass} ${className}`}
    >
      {eventType}
    </span>
  );
}
