import React from 'react';
import { AssignmentGroup } from '../../types';

interface Props {
  group: AssignmentGroup | string | null | undefined;
}

export const AssignmentBadge: React.FC<Props> = ({ group }) => {
  if (!group) return <span className="text-slate-500 text-xs font-mono">—</span>;

  const normalized = group.toLowerCase();

  if (normalized === 'treatment') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-indigo-950/60 text-indigo-300 border border-indigo-700/60">
        TREATMENT
      </span>
    );
  }

  if (normalized === 'holdout') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-zinc-900 text-zinc-400 border border-zinc-700">
        HOLDOUT
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-slate-900 text-slate-400 border border-slate-800">
      {group}
    </span>
  );
};
