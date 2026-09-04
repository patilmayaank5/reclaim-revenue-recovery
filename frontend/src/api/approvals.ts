import { fetchApi } from './client';
import { PendingApprovalItem, ActionSummary } from '../types';

export async function getPendingApprovals(): Promise<{ items: PendingApprovalItem[]; total: number }> {
  return fetchApi<{ items: PendingApprovalItem[]; total: number }>('/approvals');
}

export async function approveAction(
  actionId: string,
  approverId = 'ops_user_01',
  decisionReason = 'Approved after risk review'
): Promise<ActionSummary> {
  return fetchApi<ActionSummary>(`/actions/${actionId}/approve`, {
    method: 'POST',
    body: JSON.stringify({
      approver_id: approverId,
      decision_reason: decisionReason,
    }),
  });
}

export async function rejectAction(
  actionId: string,
  approverId = 'ops_user_01',
  decisionReason = 'Rejected due to risk penalty'
): Promise<ActionSummary> {
  return fetchApi<ActionSummary>(`/actions/${actionId}/reject`, {
    method: 'POST',
    body: JSON.stringify({
      approver_id: approverId,
      decision_reason: decisionReason,
    }),
  });
}
