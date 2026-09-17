import { Sparkles, Loader2 } from 'lucide-react';

export default function AIGenerateButton({ onClick, loading, label = 'Generate with AI' }) {
  return (
    <button onClick={onClick} disabled={loading} className="btn-primary flex items-center gap-2">
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
      {loading ? 'Generating...' : label}
    </button>
  );
}

export function DataCard({ title, children, action }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        {action}
      </div>
      {children}
    </div>
  );
}

export function EmptyState({ message, action }) {
  return (
    <div className="text-center py-12 text-gray-500">
      <p className="mb-4">{message}</p>
      {action}
    </div>
  );
}

export function StatusBadge({ status }) {
  const colors = {
    ok: 'bg-accent-100 text-accent-700',
    low: 'bg-warning-50 text-warning-600',
    critical: 'bg-danger-50 text-danger-600',
    open: 'bg-danger-50 text-danger-600',
    in_progress: 'bg-blue-100 text-blue-700',
    not_started: 'bg-gray-100 text-gray-600',
    on_hold: 'bg-warning-50 text-warning-600',
    blocked: 'bg-danger-50 text-danger-600',
    planning: 'bg-blue-100 text-blue-700',
    completed: 'bg-accent-100 text-accent-700',
    monitoring: 'bg-warning-50 text-warning-600',
    High: 'bg-danger-50 text-danger-600',
    Medium: 'bg-warning-50 text-warning-600',
    Low: 'bg-accent-100 text-accent-700',
  };
  return <span className={`badge ${colors[status] || 'bg-gray-100 text-gray-600'}`}>{String(status || '').replace(/_/g, ' ')}</span>;
}

export function ProgressBar({ value, color = 'bg-primary-600' }) {
  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${Math.min(value, 100)}%` }}></div>
    </div>
  );
}

export function formatCurrency(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val || 0);
}
