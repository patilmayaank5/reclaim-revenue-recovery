import { fetchApi } from './client';
import type { AuditEventItem } from '../types';

export interface GetAuditEventsResponse {
  items: AuditEventItem[];
  total: number;
  limit: number;
  offset: number;
}

export async function getAuditEvents(limit = 50, offset = 0): Promise<GetAuditEventsResponse> {
  const query = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString()
  });
  return fetchApi<GetAuditEventsResponse>(`/audit/events?${query.toString()}`);
}
