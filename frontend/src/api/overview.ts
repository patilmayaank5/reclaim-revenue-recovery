import { fetchApi } from './client';
import { OverviewMetrics } from '../types';

export async function getOverviewMetrics(): Promise<OverviewMetrics> {
  return fetchApi<OverviewMetrics>('/overview/metrics');
}
