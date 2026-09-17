import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import AIGenerateButton, { DataCard, EmptyState } from './shared';

function WBSNode({ node, depth, onUpdate, onRemove, parentPath }) {
  const path = [...parentPath, node.code];
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    code: node.code || '',
    name: node.name || '',
    duration_days: node.duration_days ?? '',
  });
  const [showAddChild, setShowAddChild] = useState(false);
  const [childForm, setChildForm] = useState({ code: '', name: '', duration_days: 5 });

  const saveEdit = () => {
    onUpdate(path, {
      code: form.code,
      name: form.name,
      duration_days: parseInt(form.duration_days) || 1,
    });
    setEditing(false);
  };

  const addChild = (e) => {
    e.preventDefault();
    if (!childForm.name.trim()) return;
    onUpdate(path, null, {
      code: childForm.code || `${node.code || '1'}.x`,
      name: childForm.name,
      level: (node.level || depth + 1) + 1,
        duration_days: parseInt(childForm.duration_days) || 5,
        children: [],
        user_defined: true,
      });
    setChildForm({ code: '', name: '', duration_days: 5 });
    setShowAddChild(false);
  };

  return (
    <div style={{ marginLeft: depth * 24 }} className="py-2 border-b border-gray-100">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        {editing ? (
          <div className="flex flex-wrap gap-2 flex-1 items-center">
            <input className="input-field w-24 text-sm font-mono" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
            <input className="input-field flex-1 min-w-[120px] text-sm" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input type="number" className="input-field w-20 text-sm" value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: e.target.value })} />
            <button onClick={saveEdit} className="btn-primary text-xs px-2 py-1">Save</button>
            <button onClick={() => setEditing(false)} className="btn-secondary text-xs px-2 py-1">Cancel</button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {node.code && <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded shrink-0">{node.code}</span>}
              <span className="font-medium truncate">{node.name || 'Unnamed task'}</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {node.duration_days != null && <span className="text-sm text-gray-500">{node.duration_days} days</span>}
              {(node.progress != null || node.status) && (
                <span className="text-xs text-gray-400">{Math.round(node.progress || 0)}%</span>
              )}
              <button onClick={() => setEditing(true)} className="text-xs text-primary-600 hover:underline">Edit</button>
              <button onClick={() => setShowAddChild(!showAddChild)} className="text-xs text-primary-600 hover:underline">+ Child</button>
              <button onClick={() => onRemove(path)} className="text-gray-400 hover:text-danger-500 p-1"><Trash2 className="w-4 h-4" /></button>
            </div>
          </>
        )}
      </div>
      {showAddChild && (
        <form onSubmit={addChild} className="flex flex-wrap gap-2 mt-2 ml-4">
          <input className="input-field w-24 text-sm font-mono" placeholder="Code" value={childForm.code} onChange={(e) => setChildForm({ ...childForm, code: e.target.value })} />
          <input className="input-field flex-1 min-w-[120px] text-sm" placeholder="Task name" value={childForm.name} onChange={(e) => setChildForm({ ...childForm, name: e.target.value })} required />
          <input type="number" className="input-field w-20 text-sm" placeholder="Days" value={childForm.duration_days} onChange={(e) => setChildForm({ ...childForm, duration_days: e.target.value })} />
          <button type="submit" className="btn-primary text-xs px-3">Add</button>
        </form>
      )}
      {Array.isArray(node.children) && node.children.map((child, i) => (
        <WBSNode key={child.code || i} node={child} depth={depth + 1} onUpdate={onUpdate} onRemove={onRemove} parentPath={path} />
      ))}
    </div>
  );
}

function wbsCodeKey(code) {
  if (!code) return [Infinity];
  return String(code).split('.').map((part) => {
    const n = parseInt(part, 10);
    return Number.isNaN(n) ? part : n;
  });
}

function compareWbsCodes(a, b) {
  const ka = wbsCodeKey(a);
  const kb = wbsCodeKey(b);
  const len = Math.max(ka.length, kb.length);
  for (let i = 0; i < len; i += 1) {
    const va = ka[i] ?? -1;
    const vb = kb[i] ?? -1;
    if (va < vb) return -1;
    if (va > vb) return 1;
  }
  return 0;
}

function sortWbsNodes(nodes) {
  return [...(nodes || [])]
    .sort((a, b) => compareWbsCodes(a.code, b.code))
    .map((n) => ({
      ...n,
      children: n.children?.length ? sortWbsNodes(n.children) : (n.children || []),
    }));
}

function rollupStatus(statuses, progresses) {
  if (!progresses.length) return 'not_started';
  if (progresses.every((p) => p >= 100)) return 'completed';
  if (statuses.includes('blocked')) return 'blocked';
  if (statuses.includes('on_hold')) return 'on_hold';
  if (progresses.some((p) => p > 0) || statuses.includes('in_progress')) return 'in_progress';
  return 'not_started';
}

function rollupWbs(nodes) {
  return (nodes || []).map((node) => {
    const n = { ...node };
    const children = n.children || [];
    if (!children.length) {
      n.progress = Number(n.progress) || 0;
      n.status = n.status || (n.progress >= 100 ? 'completed' : n.progress > 0 ? 'in_progress' : 'not_started');
      return n;
    }
    n.children = rollupWbs(children);
    n.duration_days = n.children.reduce((sum, c) => sum + (Number(c.duration_days) || 0), 0);
    const progresses = n.children.map((c) => Number(c.progress) || 0);
    const statuses = n.children.map((c) => c.status || rollupStatus([], [Number(c.progress) || 0]));
    n.progress = Math.round((progresses.reduce((a, b) => a + b, 0) / progresses.length) * 10) / 10;
    n.status = rollupStatus(statuses, progresses);
    return n;
  });
}

function updateAtPath(nodes, path, updates, newChild) {
  if (path.length === 0) return nodes;
  const [head, ...rest] = path;
  return nodes.map((n) => {
    if (n.code !== head) return n;
    if (rest.length === 0) {
      if (newChild) {
        return { ...n, children: [...(n.children || []), newChild] };
      }
      return { ...n, ...updates };
    }
    return { ...n, children: updateAtPath(n.children || [], rest, updates, newChild) };
  });
}

function removeAtPath(nodes, path) {
  if (path.length === 1) return nodes.filter((n) => n.code !== path[0]);
  const [head, ...rest] = path;
  return nodes.map((n) => {
    if (n.code !== head) return n;
    return { ...n, children: removeAtPath(n.children || [], rest) };
  });
}

export default function WBSTab({ data, onUpdate, onGenerate, loading, saving }) {
  const items = Array.isArray(data) ? data : [];
  const [showAddRoot, setShowAddRoot] = useState(false);
  const [rootForm, setRootForm] = useState({ code: '', name: '', duration_days: 14 });

  const handleUpdate = (path, updates, newChild) => {
    onUpdate(sortWbsNodes(rollupWbs(updateAtPath(items, path, updates, newChild))));
  };

  const handleRemove = (path) => {
    if (!confirm('Remove this WBS item and all its children?')) return;
    onUpdate(sortWbsNodes(rollupWbs(removeAtPath(items, path))));
  };

  const addRoot = (e) => {
    e.preventDefault();
    if (!rootForm.name.trim()) return;
    onUpdate(sortWbsNodes(rollupWbs([
      ...items,
      {
        code: rootForm.code || `${items.length + 1}.0`,
        name: rootForm.name,
        level: 1,
        duration_days: parseInt(rootForm.duration_days) || 14,
        children: [],
        user_defined: true,
      },
    ])));
    setRootForm({ code: '', name: '', duration_days: 14 });
    setShowAddRoot(false);
  };

  if (items.length === 0) {
    const invalid = data && !Array.isArray(data);
    return (
      <EmptyState
        message={invalid ? 'WBS data was invalid. Add tasks manually or regenerate.' : 'No Work Breakdown Structure yet.'}
        action={
          <div className="flex gap-3 justify-center flex-wrap">
            <AIGenerateButton onClick={onGenerate} loading={loading} label="Generate WBS" />
            <button onClick={() => setShowAddRoot(true)} className="btn-secondary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Add Task Manually
            </button>
          </div>
        }
      />
    );
  }

  return (
    <div>
      <div className="flex justify-end gap-3 mb-4 items-center">
        {saving && <span className="text-sm text-gray-500">Saving...</span>}
        <button onClick={() => setShowAddRoot(true)} className="btn-secondary flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> Add Top-Level Task
        </button>
        <AIGenerateButton onClick={onGenerate} loading={loading} label="Regenerate WBS" />
      </div>
      {showAddRoot && (
        <form onSubmit={addRoot} className="card mb-4 flex flex-wrap gap-2 items-end">
          <div><label className="text-xs text-gray-500">Code</label><input className="input-field w-24 font-mono" value={rootForm.code} onChange={(e) => setRootForm({ ...rootForm, code: e.target.value })} /></div>
          <div className="flex-1 min-w-[160px]"><label className="text-xs text-gray-500">Name</label><input className="input-field" value={rootForm.name} onChange={(e) => setRootForm({ ...rootForm, name: e.target.value })} required /></div>
          <div><label className="text-xs text-gray-500">Days</label><input type="number" className="input-field w-20" value={rootForm.duration_days} onChange={(e) => setRootForm({ ...rootForm, duration_days: e.target.value })} /></div>
          <button type="submit" className="btn-primary">Add</button>
          <button type="button" onClick={() => setShowAddRoot(false)} className="btn-secondary">Cancel</button>
        </form>
      )}
      <DataCard title="Work Breakdown Structure">
        {items.map((node, i) => (
          <WBSNode key={node.code || i} node={node} depth={0} onUpdate={handleUpdate} onRemove={handleRemove} parentPath={[]} />
        ))}
      </DataCard>
    </div>
  );
}
