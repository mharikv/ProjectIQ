import { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, Pencil } from 'lucide-react';
import GanttChart from './GanttChart';
import AIGenerateButton, { DataCard, EmptyState, StatusBadge } from './shared';

const STATUSES = [
  { value: 'not_started', label: 'Not Started' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'on_hold', label: 'On Hold' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'completed', label: 'Completed' },
];

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

function taskDurationDays(task) {
  if (task.duration_days != null) return Number(task.duration_days) || 0;
  if (task.start && task.end) {
    const start = new Date(task.start);
    const end = new Date(task.end);
    if (!Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime())) {
      return Math.max(1, Math.round((end - start) / 86400000) + 1);
    }
  }
  return 0;
}

function criticalPathDays(gantt) {
  if (gantt?.critical_path_duration_days != null) return gantt.critical_path_duration_days;
  const tasks = gantt?.tasks || [];
  const cpIds = new Set((gantt?.critical_path || []).map(String));
  if (!cpIds.size) return 0;
  return tasks
    .filter((t) => cpIds.has(String(t.id)))
    .reduce((sum, t) => sum + taskDurationDays(t), 0);
}

function isOnCriticalPath(task, criticalPath) {
  if (task.critical === true) return true;
  const cpSet = new Set((criticalPath || []).map(String));
  return cpSet.has(String(task.id));
}

export default function GanttTab({ data, wbs, onGenerate, loading, onTaskUpdate, onGanttUpdate, onSync, saving }) {
  const [updatingId, setUpdatingId] = useState(null);
  const [showAddMilestone, setShowAddMilestone] = useState(false);
  const [milestoneForm, setMilestoneForm] = useState({ name: '', date: '' });
  const [editingMilestone, setEditingMilestone] = useState(null);
  const syncedRef = useRef(false);

  useEffect(() => {
    if (!onSync || syncedRef.current || !data?.tasks?.length) return;
    const leaves = data.tasks.filter((t) => !t.is_summary);
    const missingMetrics = leaves.some((t) => t.float_days == null && t.critical == null);
    if (missingMetrics || !(data.critical_path?.length)) {
      syncedRef.current = true;
      onSync();
    }
  }, [data, onSync]);

  const tasks = (data?.tasks || [])
    .filter((t) => !t.is_summary)
    .sort((a, b) => compareWbsCodes(a.wbs_code, b.wbs_code));

  const milestones = data?.milestones || [];
  const cpDays = data?.critical_path_duration_days ?? criticalPathDays(data);
  const parallelGroups = data?.parallel_groups || [];
  const parallelTaskCount = parallelGroups.reduce((sum, g) => sum + (g.task_ids?.length || 0), 0);

  if (!data || !data.tasks) {
    return <EmptyState message="No Gantt schedule generated yet." action={<AIGenerateButton onClick={onGenerate} loading={loading} label="Generate Gantt Chart" />} />;
  }

  const saveGantt = (patch) => {
    if (!onGanttUpdate) return;
    onGanttUpdate({ ...data, ...patch });
  };

  const handleStatusChange = async (task, status) => {
    setUpdatingId(task.id ?? task.wbs_code);
    try {
      await onTaskUpdate({ task_id: task.id, wbs_code: task.wbs_code, status });
    } finally {
      setUpdatingId(null);
    }
  };

  const handleProgressChange = async (task, progress) => {
    const val = Math.max(0, Math.min(100, Number(progress) || 0));
    setUpdatingId(task.id ?? task.wbs_code);
    try {
      await onTaskUpdate({ task_id: task.id, wbs_code: task.wbs_code, progress: val });
    } finally {
      setUpdatingId(null);
    }
  };

  const addMilestone = (e) => {
    e.preventDefault();
    if (!milestoneForm.name.trim() || !milestoneForm.date) return;
    saveGantt({
      milestones: [
        ...milestones,
        { name: milestoneForm.name.trim(), date: milestoneForm.date, user_defined: true },
      ],
    });
    setMilestoneForm({ name: '', date: '' });
    setShowAddMilestone(false);
  };

  const saveMilestoneEdit = (e) => {
    e.preventDefault();
    if (editingMilestone == null || !milestoneForm.name.trim() || !milestoneForm.date) return;
    const updated = milestones.map((m, i) => (
      i === editingMilestone
        ? { ...m, name: milestoneForm.name.trim(), date: milestoneForm.date }
        : m
    ));
    saveGantt({ milestones: updated });
    setEditingMilestone(null);
    setMilestoneForm({ name: '', date: '' });
  };

  const startEditMilestone = (index) => {
    const m = milestones[index];
    setEditingMilestone(index);
    setMilestoneForm({ name: m.name || '', date: m.date || '' });
    setShowAddMilestone(false);
  };

  const removeMilestone = (index) => {
    if (!confirm('Remove this milestone?')) return;
    saveGantt({ milestones: milestones.filter((_, i) => i !== index) });
    if (editingMilestone === index) {
      setEditingMilestone(null);
      setMilestoneForm({ name: '', date: '' });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-4 text-sm text-gray-500 flex-wrap">
          <span>Total: <strong className="text-gray-800">{data.total_duration_days} days</strong></span>
          {(data.critical_path?.length > 0) && (
            <span>Critical Path: <strong className="text-red-600">{cpDays} days</strong></span>
          )}
          {parallelGroups.length > 0 && (
            <span>Parallel Groups: <strong className="text-indigo-600">{parallelGroups.length}</strong> ({parallelTaskCount} tasks)</span>
          )}
          <span>Tasks: <strong className="text-gray-800">{tasks.length}</strong></span>
          <span>Milestones: <strong className="text-gray-800">{milestones.length}</strong></span>
          {data.scheduling_method === 'parallel_aware_cpm' && (
            <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">Parallel-aware schedule</span>
          )}
          {saving && <span className="text-primary-600">Syncing project metrics...</span>}
        </div>
        <AIGenerateButton onClick={onGenerate} loading={loading} label="Regenerate Schedule" />
      </div>

      <DataCard title="Update Task Status & Progress">
        <p className="text-xs text-gray-500 mb-3">
          Sibling WBS tasks are scheduled in parallel where possible. Approval/review gates wait for parallel work to finish.
          Critical path is computed with CPM based on dependencies and float.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2 pr-3">Code</th>
                <th className="py-2 pr-3">Task</th>
                <th className="py-2 pr-3">Status</th>
                <th className="py-2 pr-3">Progress</th>
                <th className="py-2 pr-3">Float</th>
                <th className="py-2">Timeline</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => {
                const tid = task.id ?? task.wbs_code;
                const busy = updatingId === tid;
                const status = task.status || (task.progress >= 100 ? 'completed' : task.progress > 0 ? 'in_progress' : 'not_started');
                return (
                  <tr key={tid} className="border-b border-gray-50">
                    <td className="py-2 pr-3 font-mono text-xs text-gray-500">{task.wbs_code || '—'}</td>
                    <td className="py-2 pr-3 font-medium">{task.name}</td>
                    <td className="py-2 pr-3">
                      <select
                        className="input-field text-xs py-1"
                        value={status}
                        disabled={busy || saving}
                        onChange={(e) => handleStatusChange(task, e.target.value)}
                      >
                        {STATUSES.map((s) => (
                          <option key={s.value} value={s.value}>{s.label}</option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2 pr-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min="0"
                          max="100"
                          className="input-field w-16 text-xs py-1"
                          value={task.progress ?? 0}
                          disabled={busy || saving}
                          onChange={(e) => handleProgressChange(task, e.target.value)}
                        />
                        <span className="text-xs text-gray-400">%</span>
                      </div>
                    </td>
                    <td className="py-2 pr-3">
                      {task.float_days != null || task.critical != null ? (
                        <span className={`text-xs ${isOnCriticalPath(task, data.critical_path) ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                          {isOnCriticalPath(task, data.critical_path) ? 'Critical' : `${task.float_days ?? 0}d float`}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-300">—</span>
                      )}
                    </td>
                    <td className="py-2">
                      <StatusBadge status={status} />
                      <span className="text-xs text-gray-400 ml-2">{task.start} → {task.end}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </DataCard>

      <GanttChart
        ganttData={data}
        wbsData={wbs}
        criticalPath={data.critical_path || []}
        criticalPathDays={cpDays}
      />

      {parallelGroups.length > 0 && (
        <DataCard title="Parallel Workstreams">
          <p className="text-xs text-gray-500 mb-3">
            These task groups can run at the same time, reducing overall project duration.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {parallelGroups.map((group) => (
              <div key={group.group_code} className="p-3 rounded-lg border border-indigo-100 bg-indigo-50/50">
                <p className="font-medium text-indigo-800 text-sm">Phase {group.group_code}</p>
                <ul className="mt-1 text-xs text-indigo-700 space-y-0.5">
                  {(group.task_names || []).map((name) => (
                    <li key={name}>• {name}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </DataCard>
      )}

      <DataCard title="Milestones">
        <div className="flex justify-end mb-3">
          <button
            type="button"
            onClick={() => { setShowAddMilestone(!showAddMilestone); setEditingMilestone(null); setMilestoneForm({ name: '', date: '' }); }}
            className="btn-secondary flex items-center gap-2 text-sm"
            disabled={saving}
          >
            <Plus className="w-4 h-4" /> Add Milestone
          </button>
        </div>

        {(showAddMilestone || editingMilestone != null) && (
          <form onSubmit={editingMilestone != null ? saveMilestoneEdit : addMilestone} className="card mb-4 flex flex-wrap gap-2 items-end">
            <div className="flex-1 min-w-[160px]">
              <label className="text-xs text-gray-500">Name</label>
              <input
                className="input-field"
                value={milestoneForm.name}
                onChange={(e) => setMilestoneForm({ ...milestoneForm, name: e.target.value })}
                placeholder="Milestone name"
                required
              />
            </div>
            <div>
              <label className="text-xs text-gray-500">Date</label>
              <input
                type="date"
                className="input-field"
                value={milestoneForm.date}
                onChange={(e) => setMilestoneForm({ ...milestoneForm, date: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="btn-primary" disabled={saving}>
              {editingMilestone != null ? 'Save' : 'Add'}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => { setShowAddMilestone(false); setEditingMilestone(null); setMilestoneForm({ name: '', date: '' }); }}
            >
              Cancel
            </button>
          </form>
        )}

        {milestones.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No milestones yet. Add one to track key project dates.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {milestones.map((m, i) => (
              <div key={`${m.name}-${m.date}-${i}`} className="text-center p-3 bg-primary-50 rounded-lg border border-primary-100 relative group">
                <p className="font-medium text-primary-700 pr-14">{m.name}</p>
                <p className="text-sm text-primary-500">{m.date}</p>
                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={() => startEditMilestone(i)}
                    className="p-1 text-primary-600 hover:bg-primary-100 rounded"
                    title="Edit milestone"
                    disabled={saving}
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => removeMilestone(i)}
                    className="p-1 text-danger-500 hover:bg-danger-50 rounded"
                    title="Remove milestone"
                    disabled={saving}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </DataCard>
    </div>
  );
}
