import { useState } from 'react';
import { Plus, Trash2, Pencil } from 'lucide-react';
import AIGenerateButton, { DataCard, EmptyState, StatusBadge } from './shared';

function normalize(data) {
  if (Array.isArray(data)) return { materials: data };
  return { materials: data?.materials || [] };
}

export default function InventoryTab({ data, onUpdate, onGenerate, loading, saving }) {
  const { materials } = normalize(data);
  const [showForm, setShowForm] = useState(false);
  const [editIndex, setEditIndex] = useState(null);
  const [form, setForm] = useState({ name: '', required: 0, available: 0, unit: 'units', status: 'Pending' });

  const save = (updated) => {
    onUpdate(Array.isArray(data) ? updated.materials : { ...normalize(data), materials: updated.materials });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    const item = { ...form, required: Number(form.required), available: Number(form.available), user_defined: true };
    const next = [...materials];
    if (editIndex !== null) next[editIndex] = item;
    else next.push(item);
    save({ materials: next });
    setForm({ name: '', required: 0, available: 0, unit: 'units', status: 'Pending' });
    setShowForm(false);
    setEditIndex(null);
  };

  const startEdit = (i) => {
    setForm({ ...materials[i] });
    setEditIndex(i);
    setShowForm(true);
  };

  const remove = (i) => {
    if (!confirm('Remove this material?')) return;
    save({ materials: materials.filter((_, idx) => idx !== i) });
  };

  if (materials.length === 0 && !showForm) {
    return (
      <EmptyState
        message="No inventory plan yet."
        action={
          <div className="flex gap-3 justify-center flex-wrap">
            <AIGenerateButton onClick={onGenerate} loading={loading} label="Plan Inventory" />
            <button onClick={() => setShowForm(true)} className="btn-secondary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Add Material Manually
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
        <button onClick={() => { setShowForm(true); setEditIndex(null); setForm({ name: '', required: 0, available: 0, unit: 'units', status: 'Pending' }); }} className="btn-secondary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> Add Material
        </button>
        <AIGenerateButton onClick={onGenerate} loading={loading} label="Refresh Inventory Plan" />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card grid grid-cols-1 md:grid-cols-6 gap-3 items-end">
          <div className="md:col-span-2"><label className="text-xs text-gray-500">Material</label><input className="input-field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
          <div><label className="text-xs text-gray-500">Required</label><input type="number" className="input-field" value={form.required} onChange={(e) => setForm({ ...form, required: e.target.value })} /></div>
          <div><label className="text-xs text-gray-500">Available</label><input type="number" className="input-field" value={form.available} onChange={(e) => setForm({ ...form, available: e.target.value })} /></div>
          <div><label className="text-xs text-gray-500">Unit</label><input className="input-field" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} /></div>
          <div><label className="text-xs text-gray-500">Status</label><input className="input-field" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} /></div>
          <div className="flex gap-2 md:col-span-6">
            <button type="submit" className="btn-primary">{editIndex !== null ? 'Update' : 'Add'}</button>
            <button type="button" onClick={() => { setShowForm(false); setEditIndex(null); }} className="btn-secondary">Cancel</button>
          </div>
        </form>
      )}

      <DataCard title="Material Status">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="py-2">Material</th><th className="py-2">Required</th><th className="py-2">Available</th><th className="py-2">Status</th><th className="w-20"></th>
              </tr>
            </thead>
            <tbody>
              {materials.map((m, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-3 font-medium">{m.name}</td>
                  <td>{m.required} {m.unit}</td>
                  <td>{m.available} {m.unit}</td>
                  <td><StatusBadge status={m.status} /></td>
                  <td className="flex gap-1">
                    <button onClick={() => startEdit(i)} className="text-gray-400 hover:text-primary-600 p-1"><Pencil className="w-4 h-4" /></button>
                    <button onClick={() => remove(i)} className="text-gray-400 hover:text-danger-500 p-1"><Trash2 className="w-4 h-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataCard>
    </div>
  );
}
