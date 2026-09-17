import { useState } from 'react';
import { Plus, Trash2, Pencil } from 'lucide-react';
import AIGenerateButton, { EmptyState, StatusBadge } from './shared';

function normalize(data) {
  if (Array.isArray(data)) return data;
  return data?.risks || [];
}

const emptyRisk = { title: '', category: 'General', probability: 'Medium', impact: 'Medium', score: 4, mitigation: '' };

export default function RisksTab({ data, onUpdate, onGenerate, loading, saving }) {
  const risks = normalize(data);
  const [showForm, setShowForm] = useState(false);
  const [editIndex, setEditIndex] = useState(null);
  const [form, setForm] = useState(emptyRisk);

  const save = (items) => onUpdate(items);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    const item = { ...form, id: form.id || `risk-${Date.now()}`, score: Number(form.score) || 4, user_defined: true };
    const next = [...risks];
    if (editIndex !== null) next[editIndex] = item;
    else next.push(item);
    save(next);
    setForm(emptyRisk);
    setShowForm(false);
    setEditIndex(null);
  };

  const startEdit = (i) => {
    setForm({ ...risks[i] });
    setEditIndex(i);
    setShowForm(true);
  };

  const remove = (i) => {
    if (!confirm('Remove this risk?')) return;
    save(risks.filter((_, idx) => idx !== i));
  };

  if (risks.length === 0 && !showForm) {
    return (
      <EmptyState
        message="No risk analysis yet."
        action={
          <div className="flex gap-3 justify-center flex-wrap">
            <AIGenerateButton onClick={onGenerate} loading={loading} label="Analyze Risks" />
            <button onClick={() => setShowForm(true)} className="btn-secondary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Add Risk Manually
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
        <button onClick={() => { setShowForm(true); setEditIndex(null); setForm(emptyRisk); }} className="btn-secondary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> Add Risk
        </button>
        <AIGenerateButton onClick={onGenerate} loading={loading} label="Refresh Risk Analysis" />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="md:col-span-2"><label className="text-xs text-gray-500">Title</label><input className="input-field" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></div>
            <div><label className="text-xs text-gray-500">Category</label><input className="input-field" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></div>
            <div><label className="text-xs text-gray-500">Score</label><input type="number" className="input-field" value={form.score} onChange={(e) => setForm({ ...form, score: e.target.value })} /></div>
            <div><label className="text-xs text-gray-500">Probability</label>
              <select className="input-field" value={form.probability} onChange={(e) => setForm({ ...form, probability: e.target.value })}>
                <option>Low</option><option>Medium</option><option>High</option>
              </select>
            </div>
            <div><label className="text-xs text-gray-500">Impact</label>
              <select className="input-field" value={form.impact} onChange={(e) => setForm({ ...form, impact: e.target.value })}>
                <option>Low</option><option>Medium</option><option>High</option>
              </select>
            </div>
            <div className="md:col-span-2"><label className="text-xs text-gray-500">Mitigation</label><textarea className="input-field" rows={2} value={form.mitigation} onChange={(e) => setForm({ ...form, mitigation: e.target.value })} /></div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">{editIndex !== null ? 'Update Risk' : 'Add Risk'}</button>
            <button type="button" onClick={() => { setShowForm(false); setEditIndex(null); }} className="btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      <div className="grid gap-4">
        {risks.map((risk, i) => (
          <div key={risk.id || i} className="card">
            <div className="flex items-start justify-between mb-2">
              <div><h4 className="font-semibold">{risk.title}</h4><p className="text-sm text-gray-500">{risk.category}</p></div>
              <div className="flex gap-2 items-center">
                <StatusBadge status={risk.probability} /><StatusBadge status={risk.impact} />
                <span className="badge bg-gray-100">Score: {risk.score}</span>
                <button onClick={() => startEdit(i)} className="text-gray-400 hover:text-primary-600 p-1"><Pencil className="w-4 h-4" /></button>
                <button onClick={() => remove(i)} className="text-gray-400 hover:text-danger-500 p-1"><Trash2 className="w-4 h-4" /></button>
              </div>
            </div>
            <p className="text-sm text-gray-700"><strong>Mitigation:</strong> {risk.mitigation || '—'}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
