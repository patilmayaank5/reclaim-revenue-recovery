import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layout/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { LiveRecoveryPage } from './pages/LiveRecoveryPage';
import { CasesPage } from './pages/CasesPage';
import { CaseInvestigationPage } from './pages/CaseInvestigationPage';
import { ApprovalQueuePage } from './pages/ApprovalQueuePage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { PoliciesPage } from './pages/PoliciesPage';
import { AuditPage } from './pages/AuditPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/live-recovery" element={<LiveRecoveryPage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/cases/:caseId" element={<CaseInvestigationPage />} />
            <Route path="/approvals" element={<ApprovalQueuePage />} />
            <Route path="/experiments" element={<ExperimentsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/policies" element={<PoliciesPage />} />
            <Route path="/audit" element={<AuditPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  );
};
