import { useState } from 'react';
import { Plus, Trash2, Pencil } from 'lucide-react';
import AIGenerateButton, { EmptyState, ProgressBar } from './shared';

function normalize(data) {
  if (Array.isArray(data)) return data;
  return data?.machines || [];
}

const emptyMachine = { name: '', health_score: 100, failure_probability: 0.05, predicted_failure_date: '', recommendation: '' };

export default function MaintenanceTab({ data, onUpdate, onGenerate, loading, saving }) {
  const machines = normalize(data);
  const [showForm, setShowForm] = useState(false);
  const [editIndex, setEditIndex] = useState(null);
  const [form, setForm] = useState(emptyMachine);

  const save = (items) => {
    onUpdate(Array.isArray(data) ? items : { machines: items });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    const item = {
      ...form,
      health_score: Number(form.health_score),
      failure_probability: Number(form.failure_probability),
      user_defined: true,
    };
    const next = [...machines];
    if (editIndex !== null) next[editIndex] = item;
    else next.push(item);
    save(next);
    setForm(emptyMachine);
    setShowForm(false);
    setEditIndex(null);
  };

  const startEdit = (i) => {
    setForm({ ...machines[i] });
    setEditIndex(i);
    setShowForm(true);
  };

  const remove = (i) => {
    if (!confirm('Remove this machine?')) return;
    save(machines.filter((_, idx) => idx !== i));
  };

  if (machines.length === 0 && !showForm) {
    return (
      <EmptyState
        message="No maintenance predictions yet."
        action={
          <div className="flex gap-3 justify-center flex-wrap">
            <AIGenerateButton onClick={onGenerate} loading={loading} label="Predict Maintenance" />
            <button onClick={() => setShowForm(true)} className="btn-secondary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Add Machine Manually
            </button>
          </div>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end gap-3 items-center">
        {saving && <span className="text-sm text-gray-500">Saving...</span>}
        <button onClick={() => { setShowForm(true); setEditIndex(null); setForm(emptyMachine); }} className="btn-secondary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> Add Machine
        </button>
        <AIGenerateButton onClick={onGenerate} loading={loading} label="Refresh Predictions" />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="md:col-span-2"><label className="text-xs text-gray-500">Machine Name</label><input className="input-field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
          <div><label className="text-xs text-gray-500">Health Score (%)</label><input type="number" className="input-field" value={form.health_score} onChange={(e) => setForm({ ...form, health_score: e.target.value })} /></div>
          <div><label className="text-xs text-gray-500">Failure Probability (0–1)</label><input type="number" step="0.01" className="input-field" value={form.failure_probability} onChange={(e) => setForm({ ...form, failure_probability: e.target.value })} /></div>
          <div><label className="text-xs text-gray-500">Predicted Failure Date</label><input type="date" className="input-field" value={form.predicted_failure_date} onChange={(e) => setForm({ ...form, predicted_failure_date: e.target.value })} /></div>
          <div className="md:col-span-2"><label className="text-xs text-gray-500">Recommendation</label><textarea className="input-field" rows={2} value={form.recommendation} onChange={(e) => setForm({ ...form, recommendation: e.target.value })} /></div>
          <div className="md:col-span-2 flex gap-2">
            <button type="submit" className="btn-primary">{editIndex !== null ? 'Update' : 'Add'}</button>
            <button type="button" onClick={() => { setShowForm(false); setEditIndex(null); }} className="btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      <div className="grid gap-4">
        {machines.map((machine, i) => (
          <div key={i} className="card">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold">{machine.name}</h4>
              <div className="flex items-center gap-2">
                <span className={`badge ${machine.health_score >= 80 ? 'bg-accent-100 text-accent-700' : machine.health_score >= 60 ? 'bg-warning-50 text-warning-600' : 'bg-danger-50 text-danger-600'}`}>
                  Health: {machine.health_score}%
                </span>
                <button onClick={() => startEdit(i)} className="text-gray-400 hover:text-primary-600 p-1"><Pencil className="w-4 h-4" /></button>
                <button onClick={() => remove(i)} className="text-gray-400 hover:text-danger-500 p-1"><Trash2 className="w-4 h-4" /></button>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
              <div><p className="text-gray-500">Failure Probability</p><p className="font-medium">{((machine.failure_probability || 0) * 100).toFixed(0)}%</p></div>
              <div><p className="text-gray-500">Predicted Failure</p><p className="font-medium">{machine.predicted_failure_date || '—'}</p></div>
              <div className="md:col-span-2"><p className="text-gray-500">Recommendation</p><p className="font-medium">{machine.recommendation || '—'}</p></div>
            </div>
            <ProgressBar value={machine.health_score} color={machine.health_score >= 80 ? 'bg-accent-500' : machine.health_score >= 60 ? 'bg-warning-500' : 'bg-danger-500'} />
          </div>
        ))}
      </div>
    </div>
  );
}
