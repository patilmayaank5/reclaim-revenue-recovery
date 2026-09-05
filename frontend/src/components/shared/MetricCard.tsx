import React from 'react';

interface MetricCardProps {
  title: string;
  value: React.ReactNode;
  subtitle?: string;
  trend?: {
    value: number | string;
    isPositive: boolean;
    label?: string;
  };
  icon?: React.ReactNode;
  className?: string;
}

export function MetricCard({ title, value, subtitle, trend, icon, className = '' }: MetricCardProps) {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-lg p-5 flex flex-col justify-between ${className}`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-slate-400 text-sm font-medium">{title}</h3>
        {icon && <div className="text-slate-500">{icon}</div>}
      </div>

      <div>
        <div className="text-2xl font-semibold text-white">{value}</div>

        <div className="flex items-center mt-2 space-x-2">
          {trend && (
            <span className={`text-xs font-medium flex items-center ${trend.isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
              {trend.isPositive ? '↑' : '↓'} {trend.value}
            </span>
          )}
          {(trend?.label || subtitle) && (
            <span className="text-xs text-slate-500">
              {trend?.label || subtitle}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
