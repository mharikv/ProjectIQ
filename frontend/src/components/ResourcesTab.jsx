import { useState, useMemo } from 'react';
import { ChevronDown, ChevronRight, Plus, UserPlus, Trash2, Save, Pencil } from 'lucide-react';
import AIGenerateButton, { DataCard, EmptyState, ProgressBar } from './shared';

function normalizeResources(data) {
  if (!data) return { departments: [], recommendations: [], conflicts: [] };
  if (Array.isArray(data)) {
    return { departments: data, recommendations: [], conflicts: [] };
  }
  const items = data.departments || data.allocations || [];
  return {
    departments: items.map((r, i) => ({
      id: r.id || `dept-${i}-${Date.now()}`,
      department: r.department || r.resource || 'Unnamed Department',
      type: r.type === 'worker' ? 'department' : (r.type || 'department'),
      task: r.task || '',
      hours: r.hours ?? 0,
      utilization: r.utilization ?? 0,
      employees: r.employees || [],
    })),
    recommendations: data.recommendations || [],
    conflicts: data.conflicts || [],
  };
}

export default function ResourcesTab({ resources, onUpdate, onGenerate, loading, saving }) {
  const { departments, recommendations, conflicts } = useMemo(() => normalizeResources(resources), [resources]);
  const [expanded, setExpanded] = useState({});
  const [showAddDept, setShowAddDept] = useState(false);
  const [addEmployeeDeptId, setAddEmployeeDeptId] = useState(null);
  const [deptForm, setDeptForm] = useState({ department: '', task: '', hours: '', utilization: '' });
  const [empForm, setEmpForm] = useState({ employee_number: '', name: '', designation: '' });
  const [showAddEquip, setShowAddEquip] = useState(false);
  const [editEquipId, setEditEquipId] = useState(null);
  const [equipForm, setEquipForm] = useState({ department: '', type: 'machine', task: '', hours: '', utilization: '' });

  const isDepartment = (d) => d.type === 'department' || d.type === 'worker';

  const saveResources = (updatedDepts, extra = {}) => {
    onUpdate({
      departments: updatedDepts,
      recommendations,
      conflicts,
      ...extra,
    });
  };

  const toggleExpand = (id) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleAddDepartment = (e) => {
    e.preventDefault();
    const newDept = {
      id: `dept-${Date.now()}`,
      department: deptForm.department,
      type: 'department',
      task: deptForm.task,
      hours: parseFloat(deptForm.hours) || 0,
      utilization: parseFloat(deptForm.utilization) || 0,
      employees: [],
      user_defined: true,
    };
    saveResources([...departments, newDept]);
    setDeptForm({ department: '', task: '', hours: '', utilization: '' });
    setShowAddDept(false);
  };

  const handleAddEmployee = (e, deptId) => {
    e.preventDefault();
    const updated = departments.map((d) => {
      if (d.id !== deptId) return d;
      return {
        ...d,
        employees: [
          ...(d.employees || []),
          {
            employee_number: empForm.employee_number,
            name: empForm.name,
            designation: empForm.designation,
          },
        ],
      };
    });
    saveResources(updated);
    setEmpForm({ employee_number: '', name: '', designation: '' });
    setAddEmployeeDeptId(null);
  };

  const handleDeleteDepartment = (deptId) => {
    if (!confirm('Remove this department and all its employees?')) return;
    saveResources(departments.filter((d) => d.id !== deptId));
  };

  const handleDeleteEmployee = (deptId, empIndex) => {
    const updated = departments.map((d) => {
      if (d.id !== deptId) return d;
      return { ...d, employees: d.employees.filter((_, i) => i !== empIndex) };
    });
    saveResources(updated);
  };

  const handleAddEquipment = (e) => {
    e.preventDefault();
    if (!equipForm.department.trim()) return;
    const item = {
      id: editEquipId || `equip-${Date.now()}`,
      department: equipForm.department,
      type: equipForm.type,
      task: equipForm.task,
      hours: parseFloat(equipForm.hours) || 0,
      utilization: parseFloat(equipForm.utilization) || 0,
      employees: [],
      user_defined: true,
    };
    if (editEquipId) {
      saveResources(departments.map((d) => (d.id === editEquipId ? item : d)));
    } else {
      saveResources([...departments, item]);
    }
    setEquipForm({ department: '', type: 'machine', task: '', hours: '', utilization: '' });
    setShowAddEquip(false);
    setEditEquipId(null);
  };

  const startEditEquipment = (eq) => {
    setEquipForm({
      department: eq.department,
      type: eq.type || 'machine',
      task: eq.task || '',
      hours: eq.hours ?? '',
      utilization: eq.utilization ?? '',
    });
    setEditEquipId(eq.id);
    setShowAddEquip(true);
  };

  const handleDeleteEquipment = (eqId) => {
    if (!confirm('Remove this machine/equipment?')) return;
    saveResources(departments.filter((d) => d.id !== eqId));
  };

  const workerDepartments = departments.filter(isDepartment);
  const equipmentItems = departments.filter((d) => !isDepartment(d));

  if (departments.length === 0 && !showAddDept) {
    return (
      <div className="space-y-4">
        <EmptyState
          message="No resource allocation plan yet."
          action={
            <div className="flex gap-3 justify-center flex-wrap">
              <AIGenerateButton onClick={onGenerate} loading={loading} label="Optimize Resources" />
              <button onClick={() => setShowAddDept(true)} className="btn-secondary flex items-center gap-2">
                <Plus className="w-4 h-4" /> Add Department
              </button>
            </div>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <p className="text-sm text-gray-500">Click a department to view and manage employees</p>
        <div className="flex gap-2">
          <button onClick={() => setShowAddDept(true)} className="btn-secondary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" /> Add Department
          </button>
          <AIGenerateButton onClick={onGenerate} loading={loading} label="Re-optimize" />
        </div>
      </div>

      {showAddDept && (
        <div className="card border border-primary-200 bg-primary-50/30">
          <h3 className="font-semibold mb-3">New Department</h3>
          <form onSubmit={handleAddDepartment} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <input className="input-field" placeholder="Department name *" value={deptForm.department} onChange={(e) => setDeptForm({ ...deptForm, department: e.target.value })} required />
            <input className="input-field" placeholder="Assigned task" value={deptForm.task} onChange={(e) => setDeptForm({ ...deptForm, task: e.target.value })} />
            <input type="number" className="input-field" placeholder="Hours" value={deptForm.hours} onChange={(e) => setDeptForm({ ...deptForm, hours: e.target.value })} />
            <input type="number" className="input-field" placeholder="Utilization %" value={deptForm.utilization} onChange={(e) => setDeptForm({ ...deptForm, utilization: e.target.value })} min="0" max="100" />
            <div className="md:col-span-2 lg:col-span-4 flex gap-2">
              <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 text-sm">
                <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save Department'}
              </button>
              <button type="button" onClick={() => setShowAddDept(false)} className="btn-secondary text-sm">Cancel</button>
            </div>
          </form>
        </div>
      )}

      <DataCard title="Departments">
        <div className="divide-y divide-gray-100">
          {workerDepartments.map((dept) => {
            const isOpen = expanded[dept.id];
            const empCount = dept.employees?.length || 0;
            return (
              <div key={dept.id} className="py-1">
                <div
                  className="flex items-center gap-3 py-3 px-2 rounded-lg hover:bg-slate-50 cursor-pointer group"
                  onClick={() => toggleExpand(dept.id)}
                >
                  <button type="button" className="p-1 text-gray-400 hover:text-gray-600" onClick={(e) => { e.stopPropagation(); toggleExpand(dept.id); }}>
                    {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  <div className="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-4 gap-2 items-center">
                    <div>
                      <p className="font-semibold text-gray-900">{dept.department}</p>
                      <p className="text-xs text-gray-400">{empCount} employee{empCount !== 1 ? 's' : ''}</p>
                    </div>
                    <p className="text-sm text-gray-600 truncate">{dept.task || '—'}</p>
                    <p className="text-sm text-gray-600">{dept.hours}h</p>
                    <div className="flex items-center gap-2">
                      <ProgressBar value={dept.utilization} />
                      <span className="text-xs text-gray-500 w-10">{dept.utilization}%</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); handleDeleteDepartment(dept.id); }}
                    className="p-1.5 text-gray-300 hover:text-danger-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Delete department"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {isOpen && (
                  <div className="ml-10 mr-2 mb-4 p-4 bg-slate-50 rounded-lg border border-gray-100">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-semibold text-gray-700">Employees — {dept.department}</h4>
                      <button
                        type="button"
                        onClick={() => setAddEmployeeDeptId(addEmployeeDeptId === dept.id ? null : dept.id)}
                        className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                      >
                        <UserPlus className="w-4 h-4" /> Add Employee
                      </button>
                    </div>

                    {addEmployeeDeptId === dept.id && (
                      <form onSubmit={(e) => handleAddEmployee(e, dept.id)} className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4 p-3 bg-white rounded-lg border border-gray-200">
                        <input className="input-field text-sm" placeholder="Employee number *" value={empForm.employee_number} onChange={(e) => setEmpForm({ ...empForm, employee_number: e.target.value })} required />
                        <input className="input-field text-sm" placeholder="Full name *" value={empForm.name} onChange={(e) => setEmpForm({ ...empForm, name: e.target.value })} required />
                        <input className="input-field text-sm" placeholder="Designation *" value={empForm.designation} onChange={(e) => setEmpForm({ ...empForm, designation: e.target.value })} required />
                        <div className="md:col-span-3 flex gap-2">
                          <button type="submit" disabled={saving} className="btn-primary text-sm py-1.5 px-3">Add</button>
                          <button type="button" onClick={() => setAddEmployeeDeptId(null)} className="btn-secondary text-sm py-1.5 px-3">Cancel</button>
                        </div>
                      </form>
                    )}

                    {empCount === 0 ? (
                      <p className="text-sm text-gray-400 italic">No employees added yet.</p>
                    ) : (
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-gray-500 border-b border-gray-200">
                            <th className="py-2 pr-4">Emp. No.</th>
                            <th className="py-2 pr-4">Name</th>
                            <th className="py-2 pr-4">Designation</th>
                            <th className="py-2 w-10"></th>
                          </tr>
                        </thead>
                        <tbody>
                          {dept.employees.map((emp, idx) => (
                            <tr key={idx} className="border-b border-gray-100 last:border-0">
                              <td className="py-2.5 pr-4 font-mono text-gray-600">{emp.employee_number}</td>
                              <td className="py-2.5 pr-4 font-medium">{emp.name}</td>
                              <td className="py-2.5 pr-4 text-gray-600">{emp.designation}</td>
                              <td className="py-2.5">
                                <button type="button" onClick={() => handleDeleteEmployee(dept.id, idx)} className="text-gray-300 hover:text-danger-500">
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </DataCard>

      {equipmentItems.length > 0 && (
        <DataCard title="Machines & Equipment">
          <div className="flex justify-end mb-3">
            <button onClick={() => { setShowAddEquip(true); setEditEquipId(null); setEquipForm({ department: '', type: 'machine', task: '', hours: '', utilization: '' }); }} className="btn-secondary flex items-center gap-2 text-sm">
              <Plus className="w-4 h-4" /> Add Machine / Equipment
            </button>
          </div>
          {showAddEquip && (
            <form onSubmit={handleAddEquipment} className="card mb-4 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3 items-end border border-primary-100">
              <div className="lg:col-span-2"><label className="text-xs text-gray-500">Name</label><input className="input-field" value={equipForm.department} onChange={(e) => setEquipForm({ ...equipForm, department: e.target.value })} required /></div>
              <div><label className="text-xs text-gray-500">Type</label>
                <select className="input-field" value={equipForm.type} onChange={(e) => setEquipForm({ ...equipForm, type: e.target.value })}>
                  <option value="machine">Machine</option>
                  <option value="equipment">Equipment</option>
                </select>
              </div>
              <div><label className="text-xs text-gray-500">Task</label><input className="input-field" value={equipForm.task} onChange={(e) => setEquipForm({ ...equipForm, task: e.target.value })} /></div>
              <div><label className="text-xs text-gray-500">Hours</label><input type="number" className="input-field" value={equipForm.hours} onChange={(e) => setEquipForm({ ...equipForm, hours: e.target.value })} /></div>
              <div><label className="text-xs text-gray-500">Util %</label><input type="number" className="input-field" value={equipForm.utilization} onChange={(e) => setEquipForm({ ...equipForm, utilization: e.target.value })} /></div>
              <div className="lg:col-span-6 flex gap-2">
                <button type="submit" className="btn-primary text-sm">{editEquipId ? 'Update' : 'Add'}</button>
                <button type="button" onClick={() => { setShowAddEquip(false); setEditEquipId(null); }} className="btn-secondary text-sm">Cancel</button>
              </div>
            </form>
          )}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="py-2">Resource</th>
                  <th className="py-2">Type</th>
                  <th className="py-2">Task</th>
                  <th className="py-2">Hours</th>
                  <th className="py-2">Utilization</th>
                  <th className="w-20"></th>
                </tr>
              </thead>
              <tbody>
                {equipmentItems.map((r) => (
                  <tr key={r.id} className="border-b border-gray-50">
                    <td className="py-3 font-medium">{r.department}</td>
                    <td className="py-3 capitalize">{r.type}</td>
                    <td className="py-3">{r.task}</td>
                    <td className="py-3">{r.hours}h</td>
                    <td className="py-3"><ProgressBar value={r.utilization} /></td>
                    <td className="py-3 flex gap-1">
                      <button onClick={() => startEditEquipment(r)} className="text-gray-400 hover:text-primary-600 p-1"><Pencil className="w-4 h-4" /></button>
                      <button onClick={() => handleDeleteEquipment(r.id)} className="text-gray-400 hover:text-danger-500 p-1"><Trash2 className="w-4 h-4" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataCard>
      )}

      {equipmentItems.length === 0 && (
        <DataCard title="Machines & Equipment">
          <p className="text-sm text-gray-500 mb-3">Track machines and equipment assigned to this project.</p>
          {!showAddEquip ? (
            <button onClick={() => setShowAddEquip(true)} className="btn-secondary flex items-center gap-2 text-sm">
              <Plus className="w-4 h-4" /> Add Machine / Equipment
            </button>
          ) : (
            <form onSubmit={handleAddEquipment} className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3 items-end">
              <div className="lg:col-span-2"><label className="text-xs text-gray-500">Name</label><input className="input-field" value={equipForm.department} onChange={(e) => setEquipForm({ ...equipForm, department: e.target.value })} required /></div>
              <div><label className="text-xs text-gray-500">Type</label>
                <select className="input-field" value={equipForm.type} onChange={(e) => setEquipForm({ ...equipForm, type: e.target.value })}>
                  <option value="machine">Machine</option>
                  <option value="equipment">Equipment</option>
                </select>
              </div>
              <div><label className="text-xs text-gray-500">Task</label><input className="input-field" value={equipForm.task} onChange={(e) => setEquipForm({ ...equipForm, task: e.target.value })} /></div>
              <div><label className="text-xs text-gray-500">Hours</label><input type="number" className="input-field" value={equipForm.hours} onChange={(e) => setEquipForm({ ...equipForm, hours: e.target.value })} /></div>
              <div><label className="text-xs text-gray-500">Util %</label><input type="number" className="input-field" value={equipForm.utilization} onChange={(e) => setEquipForm({ ...equipForm, utilization: e.target.value })} /></div>
              <div className="lg:col-span-6 flex gap-2">
                <button type="submit" className="btn-primary text-sm">Add</button>
                <button type="button" onClick={() => setShowAddEquip(false)} className="btn-secondary text-sm">Cancel</button>
              </div>
            </form>
          )}
        </DataCard>
      )}

      {(recommendations.length > 0 || conflicts.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {recommendations.length > 0 && (
            <DataCard title="AI Recommendations">
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                {recommendations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </DataCard>
          )}
          {conflicts.length > 0 && (
            <DataCard title="Scheduling Conflicts">
              {conflicts.map((c, i) => (
                <div key={i} className="text-sm border-b border-gray-100 py-2 last:border-0">
                  <p className="font-medium text-danger-600">{c.resource || c.department}: {c.issue}</p>
                  <p className="text-gray-600">{c.resolution}</p>
                </div>
              ))}
            </DataCard>
          )}
        </div>
      )}
    </div>
  );
}
