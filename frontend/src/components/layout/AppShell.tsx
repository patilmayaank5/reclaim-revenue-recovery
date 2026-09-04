import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  FolderKanban,
  CheckSquare,
  FlaskConical,
  BarChart3,
  ShieldCheck,
  History,
  Menu,
  X,
  Shield,
  Zap,
} from 'lucide-react';

interface AppShellProps {
  children: React.ReactNode;
}

interface NavItem {
  label: string;
  to: string;
  icon: React.ElementType;
  placeholder?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Control Room Overview';
    if (path === '/live-recovery') return 'Live Recovery Timeline';
    if (path === '/cases') return 'Case Operations';
    if (path.startsWith('/cases/')) return 'Case Investigation';
    if (path === '/approvals') return 'Human Approval Queue';
    if (path === '/experiments') return 'Experiments (Phase 11)';
    if (path === '/analytics') return 'Analytics & Reporting (Phase 11)';
    if (path === '/policies') return 'Policy Configuration (Phase 11)';
    if (path === '/audit') return 'Audit Log Explorer (Phase 11)';
    return 'Reclaim Intelligence Engine';
  };

  const navSections: NavSection[] = [
    {
      title: 'OPERATIONS',
      items: [
        { label: 'Overview', to: '/', icon: LayoutDashboard },
        { label: 'Live Recovery', to: '/live-recovery', icon: Activity },
        { label: 'Cases', to: '/cases', icon: FolderKanban },
        { label: 'Approval Queue', to: '/approvals', icon: CheckSquare },
      ],
    },
    {
      title: 'INSIGHTS',
      items: [
        { label: 'Experiments', to: '/experiments', icon: FlaskConical },
        { label: 'Analytics', to: '/analytics', icon: BarChart3 },
      ],
    },
    {
      title: 'GOVERNANCE',
      items: [
        { label: 'Policies', to: '/policies', icon: ShieldCheck },
        { label: 'Audit', to: '/audit', icon: History },
      ],
    },
  ];

  return (
    <div className="min-h-screen flex bg-[#090d16] text-slate-100">
      {/* Sidebar Desktop */}
      <aside className="hidden lg:flex flex-col w-64 border-r border-[#1f293d] bg-[#0c121e] shrink-0">
        {/* Brand Header */}
        <div className="h-16 px-6 flex items-center border-b border-[#1f293d] bg-[#090d16]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-sm tracking-wide text-slate-100 flex items-center gap-1.5">
                RECLAIM
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/60 font-mono">
                  v1.0
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono">Revenue Recovery Engine</p>
            </div>
          </div>
        </div>

        {/* Nav Links */}
        <div className="flex-1 py-4 px-3 overflow-y-auto space-y-6">
          {navSections.map((sec) => (
            <div key={sec.title}>
              <div className="px-3 mb-2 text-[10px] font-mono font-semibold text-slate-500 tracking-wider">
                {sec.title}
              </div>
              <div className="space-y-0.5">
                {sec.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.to === '/'}
                      className={({ isActive }) =>
                        `flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                          isActive
                            ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-[#151d2d]'
                        }`
                      }
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className="w-4 h-4" />
                        <span>{item.label}</span>
                      </div>
                      {item.placeholder && (
                        <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          P11
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Footer info */}
        <div className="p-4 border-t border-[#1f293d] bg-[#090d16] text-[11px] font-mono text-slate-500 flex items-center justify-between">
          <span className="flex items-center gap-1 text-emerald-400">
            <Zap className="w-3 h-3" /> Engine Active
          </span>
          <span>Razorpay Buildathon</span>
        </div>
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="relative w-64 bg-[#0c121e] border-r border-[#1f293d] flex flex-col z-10">
            <div className="h-16 px-4 flex items-center justify-between border-b border-[#1f293d]">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-indigo-400" />
                <span className="font-bold text-sm">RECLAIM</span>
              </div>
              <button onClick={() => setMobileOpen(false)} className="text-slate-400 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 p-3 overflow-y-auto space-y-6">
              {navSections.map((sec) => (
                <div key={sec.title}>
                  <div className="px-3 mb-1 text-[10px] font-mono text-slate-500">{sec.title}</div>
                  {sec.items.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      onClick={() => setMobileOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center gap-2.5 px-3 py-2 rounded text-xs ${
                          isActive ? 'bg-indigo-600/20 text-indigo-300' : 'text-slate-400'
                        }`
                      }
                    >
                      <item.icon className="w-4 h-4" />
                      <span>{item.label}</span>
                    </NavLink>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Content Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 px-4 lg:px-8 border-b border-[#1f293d] bg-[#0c121e]/80 backdrop-blur flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-base font-semibold text-slate-100 tracking-tight">{getPageTitle()}</h1>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Simulator Mode: Active
            </span>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
};
