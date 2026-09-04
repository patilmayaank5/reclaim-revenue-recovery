import { fetchApi } from './client';
import { CaseItem, CaseInvestigationDetail } from '../types';

export async function getCases(params?: {
  status?: string;
  assignment_group?: string;
  search?: string;
}): Promise<{ items: CaseItem[]; total: number }> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status', params.status);
  if (params?.assignment_group) query.append('assignment_group', params.assignment_group);
  if (params?.search) query.append('search', params.search);

  const queryStr = query.toString();
  const endpoint = `/cases${queryStr ? `?${queryStr}` : ''}`;
  return fetchApi<{ items: CaseItem[]; total: number }>(endpoint);
}

export async function getCaseInvestigation(caseId: string): Promise<CaseInvestigationDetail> {
  return fetchApi<CaseInvestigationDetail>(`/cases/${caseId}/investigation`);
}

export async function prepareCase(caseId: string): Promise<any> {
  return fetchApi(`/cases/${caseId}/prepare`, { method: 'POST' });
}

export async function diagnoseCase(caseId: string): Promise<any> {
  return fetchApi(`/ai/cases/${caseId}/diagnose`, { method: 'POST' });
}

export async function generateInterventions(caseId: string): Promise<any> {
  return fetchApi(`/cases/${caseId}/interventions`, { method: 'POST' });
}

export async function evaluatePolicy(caseId: string): Promise<any> {
  return fetchApi(`/cases/${caseId}/policy`, { method: 'POST' });
}

export async function createAction(caseId: string, provider = 'simulator'): Promise<any> {
  return fetchApi(`/cases/${caseId}/actions?provider=${provider}`, { method: 'POST' });
}
