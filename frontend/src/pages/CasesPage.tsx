import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getCases } from '../api/cases';
import { formatMoneyMinor, formatTimestamp } from '../lib/formatters';
import { CaseStatusBadge } from '../components/status/CaseStatusBadge';
import { ActionStatusBadge } from '../components/status/ActionStatusBadge';
import { AssignmentBadge } from '../components/status/AssignmentBadge';
import { VerificationStatusBadge } from '../components/status/VerificationStatusBadge';
import { Search, Filter, FolderKanban, ArrowRight, Loader2, RefreshCcw } from 'lucide-react';

export const CasesPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [assignmentFilter, setAssignmentFilter] = useState('');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['cases-list', statusFilter, assignmentFilter, search],
    queryFn: () =>
      getCases({
        status: statusFilter || undefined,
        assignment_group: assignmentFilter || undefined,
        search: search || undefined,
      }),
  });

  const cases = data?.items || [];

  return (
    <div className="space-y-6">
      {/* Search & Filter Control Bar */}
      <div className="p-4 rounded-lg bg-[#0c121e] border border-[#1f293d] flex flex-col md:flex-row gap-4 justify-between items-stretch md:items-center">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Case ID, Payment Ref, Failure Category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 rounded bg-[#111827] border border-[#1f293d] text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
            <Filter className="w-3.5 h-3.5" /> Filter:
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded bg-[#111827] border border-[#1f293d] text-xs font-mono text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Case Statuses</option>
            <option value="detected">Detected</option>
            <option value="enriched">Enriched</option>
            <option value="diagnosed">Diagnosed</option>
            <option value="action_pending">Action Pending</option>
            <option value="action_executing">Executing</option>
            <option value="action_executed">Executed</option>
            <option value="verifying">Verifying</option>
            <option value="recovered">Recovered</option>
            <option value="not_recovered">Not Recovered</option>
            <option value="stopped">Stopped</option>
          </select>

          <select
            value={assignmentFilter}
            onChange={(e) => setAssignmentFilter(e.target.value)}
            className="px-3 py-1.5 rounded bg-[#111827] border border-[#1f293d] text-xs font-mono text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Assignment Groups</option>
            <option value="treatment">Treatment</option>
            <option value="holdout">Holdout</option>
          </select>
        </div>
      </div>

      {/* Cases Table */}
      <div className="p-5 rounded-lg bg-[#0c121e] border border-[#1f293d]">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
            <p className="text-sm font-mono">Loading Recovery Cases...</p>
          </div>
        ) : isError ? (
          <div className="text-center py-12 text-rose-400 font-mono text-xs space-y-3">
            <p>Failed to load cases from backend API.</p>
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-rose-950/60 border border-rose-800 text-rose-200"
            >
              <RefreshCcw className="w-3.5 h-3.5" /> Retry Request
            </button>
          </div>
        ) : cases.length === 0 ? (
          <div className="text-center py-16 text-slate-400 font-mono text-xs space-y-2">
            <FolderKanban className="w-10 h-10 mx-auto text-slate-600 mb-2" />
            <p className="font-semibold text-slate-300">No Recovery Cases Found</p>
            <p className="text-slate-500">Try adjusting your search terms or filter criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#111827] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1f293d]">
                <tr>
                  <th className="p-3">Case ID</th>
                  <th className="p-3">Payment Reference</th>
                  <th className="p-3">Amount at Risk</th>
                  <th className="p-3">Failure Category</th>
                  <th className="p-3">Assignment</th>
                  <th className="p-3">Case Status</th>
                  <th className="p-3">Action Status</th>
                  <th className="p-3">Verification</th>
                  <th className="p-3">Detected</th>
                  <th className="p-3 text-right">Investigate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f293d] text-slate-300">
                {cases.map((c) => (
                  <tr key={c.id} className="hover:bg-[#151d2d] transition">
                    <td className="p-3 font-semibold text-indigo-400">
                      <Link to={`/cases/${c.id}`} className="hover:underline">
                        {c.id.substring(0, 8)}...
                      </Link>
                    </td>
                    <td className="p-3 text-slate-300">{c.payment?.external_id || 'â€”'}</td>
                    <td className="p-3 font-bold text-slate-100">
                      {formatMoneyMinor(c.amount_at_risk_minor, c.currency)}
                    </td>
                    <td className="p-3 text-slate-400">{c.failure_category || 'Unclassified'}</td>
                    <td className="p-3">
                      <AssignmentBadge group={c.assignment_group} />
                    </td>
                    <td className="p-3">
                      <CaseStatusBadge status={c.status} />
                    </td>
                    <td className="p-3">
                      {c.action ? <ActionStatusBadge status={c.action.status} /> : <span className="text-slate-500">â€”</span>}
                    </td>
                    <td className="p-3">
                      <VerificationStatusBadge status={c.verification?.status} />
                    </td>
                    <td className="p-3 text-slate-400">{formatTimestamp(c.detected_at)}</td>
                    <td className="p-3 text-right">
                      <Link
                        to={`/cases/${c.id}`}
                        className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 font-sans font-medium"
                      >
                        Open <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
