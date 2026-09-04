import React from 'react';
import { PolicyOutcome } from '../../types';
import { ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react';

interface Props {
  outcome: PolicyOutcome | string | null | undefined;
}

export const PolicyOutcomeBadge: React.FC<Props> = ({ outcome }) => {
  if (!outcome) return <span className="text-slate-500 text-xs font-mono">â€”</span>;

  const normalized = outcome.toLowerCase();

  switch (normalized) {
    case 'allow_auto':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950/50 text-emerald-300 border border-emerald-700/50">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          ALLOW_AUTO
        </span>
      );
    case 'require_approval':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-950/60 text-amber-300 border border-amber-700/60">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          REQUIRE_APPROVAL
        </span>
      );
    case 'block':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold bg-rose-950/60 text-rose-300 border border-rose-700/60">
          <ShieldX className="w-3.5 h-3.5 text-rose-400" />
          BLOCK
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-slate-900 text-slate-300 border border-slate-800">
          {outcome}
        </span>
      );
  }
};
