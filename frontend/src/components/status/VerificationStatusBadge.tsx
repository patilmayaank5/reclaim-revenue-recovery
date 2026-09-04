import React from 'react';
import { VerificationStatus } from '../../types';
import { CheckCircle2, XCircle, Clock, AlertTriangle } from 'lucide-react';

interface Props {
  status: VerificationStatus | string | null | undefined;
}

export const VerificationStatusBadge: React.FC<Props> = ({ status }) => {
  if (!status) {
    return <span className="text-slate-500 text-xs font-mono">â€”</span>;
  }

  const normalized = status.toLowerCase();

  switch (normalized) {
    case 'verified_recovered':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950/70 text-emerald-300 border border-emerald-600/60">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          Verified Recovered
        </span>
      );
    case 'verified_not_recovered':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-rose-950/60 text-rose-300 border border-rose-700/60">
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          Not Recovered
        </span>
      );
    case 'pending':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-amber-950/50 text-amber-300 border border-amber-800/50">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          Verification Pending
        </span>
      );
    case 'verification_failed':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-red-950/50 text-red-300 border border-red-800/50">
          <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
          Verification Failed
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-slate-900 text-slate-400 border border-slate-800">
          {status}
        </span>
      );
  }
};
