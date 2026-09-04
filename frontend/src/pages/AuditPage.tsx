import React, { useEffect, useState } from 'react';
import { getAuditEvents } from '../api/audit';
import { AuditEventItem } from '../types';
import { AuditEventTypeBadge } from '../components/status/AuditEventTypeBadge';

export function AuditPage() {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Filters
  const [eventType, setEventType] = useState('');
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getAuditEvents(50, 0);
        setEvents(data.items);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredEvents = events.filter(ev => {
    if (eventType && !ev.event_type.toLowerCase().includes(eventType.toLowerCase())) return false;
    if (entityType && !ev.entity_type.toLowerCase().includes(entityType.toLowerCase())) return false;
    if (entityId && !ev.entity_id.toLowerCase().includes(entityId.toLowerCase())) return false;
    return true;
  });

  if (loading) {
    return <div className="p-8 text-slate-400">Loading audit logs...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-white">System Audit Log</h1>
          <p className="text-sm text-slate-400 mt-1">Immutable trail of all system actions</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex gap-4">
        <input
          type="text"
          placeholder="Filter by Event Type"
          value={eventType}
          onChange={e => setEventType(e.target.value)}
          className="bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        />
        <input
          type="text"
          placeholder="Filter by Entity Type"
          value={entityType}
          onChange={e => setEntityType(e.target.value)}
          className="bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        />
        <input
          type="text"
          placeholder="Filter by Entity ID"
          value={entityId}
          onChange={e => setEntityId(e.target.value)}
          className="bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
        />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/50 text-slate-400">
              <tr>
                <th className="px-6 py-3 font-medium">Timestamp</th>
                <th className="px-6 py-3 font-medium">Event</th>
                <th className="px-6 py-3 font-medium">Entity</th>
                <th className="px-6 py-3 font-medium">Actor</th>
                <th className="px-6 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-slate-300">
              {filteredEvents.map((ev) => (
                <React.Fragment key={ev.id}>
                  <tr className="hover:bg-slate-800/20">
                    <td className="px-6 py-4 whitespace-nowrap text-slate-400">
                      {new Date(ev.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <AuditEventTypeBadge eventType={ev.event_type} />
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-xs text-slate-500 mr-2">{ev.entity_type}</span>
                      <span className="font-mono text-xs">{ev.entity_id}</span>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">
                      {ev.actor}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setExpandedId(expandedId === ev.id ? null : ev.id)}
                        className="text-indigo-400 hover:text-indigo-300 text-xs"
                      >
                        {expandedId === ev.id ? 'Hide Details' : 'View Details'}
                      </button>
                    </td>
                  </tr>
                  {expandedId === ev.id && (
                    <tr>
                      <td colSpan={5} className="px-6 py-4 bg-slate-950/50">
                        <pre className="text-xs text-slate-400 font-mono overflow-x-auto p-4 rounded bg-slate-900 border border-slate-800">
                          {JSON.stringify(ev.event_data, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
              {filteredEvents.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                    No audit events found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
