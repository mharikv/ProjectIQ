import { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import AIGenerateButton, { DataCard, EmptyState, StatusBadge } from './shared';

const LIST_SECTIONS = [
  { key: 'objectives', label: 'Objective' },
  { key: 'deliverables', label: 'Deliverable' },
  { key: 'success_criteria', label: 'Success Criterion' },
  { key: 'constraints', label: 'Constraint' },
  { key: 'assumptions', label: 'Assumption' },
];

export default function CharterTab({ data, onUpdate, onGenerate, loading, saving }) {
  const [charter, setCharter] = useState(data || {});
  const [newItems, setNewItems] = useState({});
  const [stakeholderForm, setStakeholderForm] = useState({ name: '', role: '', interest: 'Medium' });
  const [showStakeholderForm, setShowStakeholderForm] = useState(false);

  useEffect(() => {
    setCharter(data || {});
  }, [data]);

  const update = (next) => {
    setCharter(next);
    onUpdate(next);
  };

  const addListItem = (section) => {
    const val = (newItems[section] || '').trim();
    if (!val) return;
    const items = [...(charter[section] || []), val];
    update({ ...charter, [section]: items });
    setNewItems({ ...newItems, [section]: '' });
  };

  const removeListItem = (section, index) => {
    const items = [...(charter[section] || [])];
    items.splice(index, 1);
    update({ ...charter, [section]: items });
  };

  const addStakeholder = (e) => {
    e.preventDefault();
    if (!stakeholderForm.name.trim()) return;
    update({
      ...charter,
      stakeholders: [...(charter.stakeholders || []), { ...stakeholderForm }],
    });
    setStakeholderForm({ name: '', role: '', interest: 'Medium' });
    setShowStakeholderForm(false);
  };

  const removeStakeholder = (index) => {
    const stakeholders = [...(charter.stakeholders || [])];
    stakeholders.splice(index, 1);
    update({ ...charter, stakeholders });
  };

  const startEmpty = () => {
    update({
      scope: '',
      objectives: [],
      deliverables: [],
      stakeholders: [],
      success_criteria: [],
      constraints: [],
      assumptions: [],
    });
  };

  if (!data || Object.keys(data).length === 0) {
    return (
      <EmptyState
        message="No project charter yet."
        action={
          <div className="flex gap-3 justify-center flex-wrap">
            <AIGenerateButton onClick={onGenerate} loading={loading} label="Generate Project Charter" />
            <button onClick={startEmpty} className="btn-secondary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Create Manually
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
        <AIGenerateButton onClick={onGenerate} loading={loading} label="Regenerate Charter" />
      </div>

      <DataCard title="Scope">
        <textarea
          className="input-field w-full"
          rows={4}
          value={charter.scope || ''}
          onChange={(e) => setCharter({ ...charter, scope: e.target.value })}
          onBlur={() => onUpdate({ ...charter, scope: charter.scope })}
          placeholder="Project scope..."
        />
      </DataCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {LIST_SECTIONS.map(({ key, label }) => (
          <DataCard key={key} title={label + 's'}>
            <ul className="space-y-2 mb-3">
              {(charter[key] || []).map((item, i) => (
                <li key={i} className="flex items-start justify-between gap-2 text-gray-700">
                  <span className="flex-1">{item}</span>
                  <button onClick={() => removeListItem(key, i)} className="text-gray-400 hover:text-danger-500 p-1">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ul>
            <div className="flex gap-2">
              <input
                className="input-field flex-1 text-sm"
                placeholder={`Add ${label.toLowerCase()}...`}
                value={newItems[key] || ''}
                onChange={(e) => setNewItems({ ...newItems, [key]: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addListItem(key))}
              />
              <button onClick={() => addListItem(key)} className="btn-secondary px-3">
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </DataCard>
        ))}
      </div>

      <DataCard title="Stakeholders">
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Name</th>
                <th className="text-left py-2">Role</th>
                <th className="text-left py-2">Interest</th>
                <th className="w-10"></th>
              </tr>
            </thead>
            <tbody>
              {(charter.stakeholders || []).map((s, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-2">{s.name}</td>
                  <td>{s.role}</td>
                  <td><StatusBadge status={s.interest} /></td>
                  <td>
                    <button onClick={() => removeStakeholder(i)} className="text-gray-400 hover:text-danger-500">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {showStakeholderForm ? (
          <form onSubmit={addStakeholder} className="grid grid-cols-1 md:grid-cols-4 gap-2">
            <input className="input-field" placeholder="Name" value={stakeholderForm.name} onChange={(e) => setStakeholderForm({ ...stakeholderForm, name: e.target.value })} required />
            <input className="input-field" placeholder="Role" value={stakeholderForm.role} onChange={(e) => setStakeholderForm({ ...stakeholderForm, role: e.target.value })} />
            <select className="input-field" value={stakeholderForm.interest} onChange={(e) => setStakeholderForm({ ...stakeholderForm, interest: e.target.value })}>
              <option>High</option><option>Medium</option><option>Low</option>
            </select>
            <div className="flex gap-2">
              <button type="submit" className="btn-primary flex-1">Add</button>
              <button type="button" onClick={() => setShowStakeholderForm(false)} className="btn-secondary">Cancel</button>
            </div>
          </form>
        ) : (
          <button onClick={() => setShowStakeholderForm(true)} className="btn-secondary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" /> Add Stakeholder
          </button>
        )}
      </DataCard>
    </div>
  );
}
