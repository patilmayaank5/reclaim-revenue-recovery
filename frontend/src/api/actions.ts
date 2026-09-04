import { fetchApi } from './client';

export async function executeAction(actionId: string): Promise<any> {
  return fetchApi(`/actions/${actionId}/execute`, { method: 'POST' });
}

export async function verifyAction(actionId: string, providerScenario?: string): Promise<any> {
  const body = providerScenario ? { verification_scenario: providerScenario } : {};
  return fetchApi(`/actions/${actionId}/verify`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}
