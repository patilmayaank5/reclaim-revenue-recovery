import { fetchApi } from './client';

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
}

export interface DemoRunResult {
  case_id: string;
  action_id?: string;
  status: string;
}

export interface DemoStatus {
  is_active: boolean;
  demo_cases_count: number;
}

export async function getDemoScenarios(): Promise<{ scenarios: DemoScenario[] }> {
  return fetchApi<{ scenarios: DemoScenario[] }>('/demo/scenarios');
}

export async function runDemoScenario(scenarioId: string): Promise<DemoRunResult> {
  return fetchApi<DemoRunResult>(`/demo/scenarios/${scenarioId}/run`, {
    method: 'POST',
  });
}

export async function resetDemo(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>('/demo/reset', {
    method: 'POST',
  });
}

export async function getDemoStatus(): Promise<DemoStatus> {
  return fetchApi<DemoStatus>('/demo/status');
}
