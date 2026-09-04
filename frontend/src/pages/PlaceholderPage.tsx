import React from 'react';
import { Lock, Clock } from 'lucide-react';

interface Props {
  title: string;
  description: string;
  phase?: string;
}

export const PlaceholderPage: React.FC<Props> = ({ title, description, phase = 'Phase 11' }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[450px] p-8 rounded-lg bg-[#0c121e] border border-[#1f293d] text-center max-w-xl mx-auto space-y-4">
      <div className="w-12 h-12 rounded-full bg-indigo-950/60 border border-indigo-700/50 flex items-center justify-center text-indigo-400">
        <Lock className="w-6 h-6" />
      </div>

      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-xs font-mono text-indigo-300">
        <Clock className="w-3.5 h-3.5" /> Scheduled for {phase}
      </div>

      <h2 className="text-xl font-bold text-slate-100">{title}</h2>
      <p className="text-xs text-slate-400 font-mono leading-relaxed max-w-md">{description}</p>

      <div className="pt-4 border-t border-[#1f293d] w-full text-[11px] font-mono text-slate-500">
        Reclaim Revenue Recovery Intelligence Engine &bull; {phase} Roadmap
      </div>
    </div>
  );
};
