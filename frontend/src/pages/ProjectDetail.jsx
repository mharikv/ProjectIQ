import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { projectsAPI, aiAPI } from '../api';
import { getApiErrorMessage, log } from '../utils/logger';
import Chatbot from '../components/Chatbot';
import GanttChart from '../components/GanttChart';
import GanttTab from '../components/GanttTab';
import ResourcesTab from '../components/ResourcesTab';
import CharterTab from '../components/CharterTab';
import WBSTab from '../components/WBSTab';
import InventoryTab from '../components/InventoryTab';
import RisksTab from '../components/RisksTab';
import MaintenanceTab from '../components/MaintenanceTab';
import AIGenerateButton, { DataCard, EmptyState, StatusBadge, ProgressBar, formatCurrency } from '../components/shared';
import {
  ArrowLeft, Settings, FileText, GitBranch, GanttChart as GanttChartIcon, Users, DollarSign,
  Package, ShieldAlert, CheckCircle, Wrench, BarChart3, MessageSquare, Save, Trash2, Download
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

const tabs = [
  { id: 'overview', label: 'Overview', icon: Settings },
  { id: 'charter', label: 'Charter', icon: FileText },
  { id: 'wbs', label: 'WBS', icon: GitBranch },
  { id: 'gantt', label: 'Gantt', icon: GanttChartIcon },
  { id: 'resources', label: 'Resources', icon: Users },
  { id: 'budget', label: 'Budget', icon: DollarSign },
  { id: 'inventory', label: 'Inventory', icon: Package },
  { id: 'risks', label: 'Risks', icon: ShieldAlert },
  { id: 'quality', label: 'Quality', icon: CheckCircle },
  { id: 'maintenance', label: 'Maintenance', icon: Wrench },
  { id: 'kpis', label: 'KPIs', icon: BarChart3 },
  { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
];

const CHART_COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function ProjectDetail() {
  const { id, tab = 'overview' } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [aiError, setAiError] = useState('');
  const [fieldSaving, setFieldSaving] = useState({});
  const [downloadingReport, setDownloadingReport] = useState(false);

  useEffect(() => { loadProject(); }, [id]);

  const loadProject = async () => {
    try {
      const { data } = await projectsAPI.get(id);
      setProject(data);
      setEditForm({
        name: data.name, description: data.description || '', status: data.status,
        priority: data.priority, budget: data.budget, actual_cost: data.actual_cost,
        start_date: data.start_date || '', end_date: data.end_date || '',
      });
    } catch {
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const { data } = await projectsAPI.update(id, {
        ...editForm,
        budget: parseFloat(editForm.budget) || 0,
        actual_cost: parseFloat(editForm.actual_cost) || 0,
        start_date: editForm.start_date || null,
        end_date: editForm.end_date || null,
      });
      setProject(data);
    } catch {
      alert('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await projectsAPI.delete(id);
      const view = ['completed', 'cancelled'].includes(project?.status) ? 'completed' : 'in_progress';
      navigate(`/?view=${view}`);
    } catch {
      alert('Failed to delete project');
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleDownloadReport = async () => {
    setDownloadingReport(true);
    try {
      const { data } = await projectsAPI.downloadReportPptx(id);
      const url = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement('a');
      link.href = url;
      const safeName = (project?.name || 'Project').replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '_').slice(0, 60);
      link.setAttribute('download', `${safeName}_Report.pptx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Failed to download project report. Make sure the backend is running.');
    } finally {
      setDownloadingReport(false);
    }
  };

  const handleResourcesUpdate = async (resourcesData) => {
    await handleFieldUpdate('resources', resourcesData);
  };

  const handleFieldUpdate = async (field, value) => {
    setFieldSaving((s) => ({ ...s, [field]: true }));
    try {
      const { data } = await projectsAPI.update(id, { [field]: value });
      setProject(data);
    } catch {
      alert(`Failed to save ${field}`);
    } finally {
      setFieldSaving((s) => ({ ...s, [field]: false }));
    }
  };

  const handleTaskUpdate = async (taskUpdate) => {
    setFieldSaving((s) => ({ ...s, gantt: true }));
    try {
      const { data } = await projectsAPI.updateGanttTask(id, taskUpdate);
      setProject(data);
      setEditForm((f) => ({
        ...f,
        actual_cost: data.actual_cost,
        status: data.status,
      }));
    } catch {
      alert('Failed to update task');
    } finally {
      setFieldSaving((s) => ({ ...s, gantt: false }));
    }
  };

  const handleGanttSync = async () => {
    setFieldSaving((s) => ({ ...s, gantt: true }));
    try {
      const { data } = await projectsAPI.syncProject(id);
      setProject(data);
    } catch {
      alert('Failed to refresh schedule metrics');
    } finally {
      setFieldSaving((s) => ({ ...s, gantt: false }));
    }
  };

  const runAI = async (apiFn, field) => {
    setAiLoading(true);
    setAiError('');
    try {
      log.info('Running AI feature, field=', field);
      await apiFn(id);
      const { data } = await projectsAPI.get(id);
      setProject(data);
      log.info('AI feature completed for field=', field);
    } catch (err) {
      const message = getApiErrorMessage(err, 'AI generation failed');
      setAiError(message);
      log.error('AI feature failed:', message);
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div></div>;
  if (!project) return null;

  const backView = ['completed', 'cancelled'].includes(project.status) ? 'completed' : 'in_progress';

  const renderTab = () => {
    switch (tab) {
      case 'overview': return <OverviewTab project={project} editForm={editForm} setEditForm={setEditForm} onSave={handleSave} saving={saving} onDelete={() => setShowDeleteConfirm(true)} />;
      case 'charter': return (
        <CharterTab
          data={project.charter}
          onUpdate={(val) => handleFieldUpdate('charter', val)}
          onGenerate={() => runAI(aiAPI.generateCharter, 'charter')}
          loading={aiLoading}
          saving={fieldSaving.charter}
        />
      );
      case 'wbs': return (
        <WBSTab
          data={project.wbs}
          onUpdate={(val) => handleFieldUpdate('wbs', val)}
          onGenerate={() => runAI(aiAPI.generateWBS, 'wbs')}
          loading={aiLoading}
          saving={fieldSaving.wbs}
        />
      );
      case 'gantt': return (
        <GanttTab
          data={project.gantt}
          wbs={project.wbs}
          onGenerate={() => runAI(aiAPI.generateGantt, 'gantt')}
          loading={aiLoading}
          onTaskUpdate={handleTaskUpdate}
          onGanttUpdate={(val) => handleFieldUpdate('gantt', val)}
          onSync={handleGanttSync}
          saving={fieldSaving.gantt}
        />
      );
      case 'resources': return (
        <ResourcesTab
          resources={project.resources}
          onUpdate={handleResourcesUpdate}
          onGenerate={() => runAI(aiAPI.optimizeResources, 'resources')}
          loading={aiLoading}
          saving={fieldSaving.resources}
        />
      );
      case 'budget': return <BudgetTab data={project.budget_details} project={project} onGenerate={() => runAI(aiAPI.analyzeBudget, 'budget_details')} loading={aiLoading} />;
      case 'inventory': return (
        <InventoryTab
          data={project.inventory}
          onUpdate={(val) => handleFieldUpdate('inventory', val)}
          onGenerate={() => runAI(aiAPI.planInventory, 'inventory')}
          loading={aiLoading}
          saving={fieldSaving.inventory}
        />
      );
      case 'risks': return (
        <RisksTab
          data={project.risks}
          onUpdate={(val) => handleFieldUpdate('risks', val)}
          onGenerate={() => runAI(aiAPI.analyzeRisks, 'risks')}
          loading={aiLoading}
          saving={fieldSaving.risks}
        />
      );
      case 'quality': return <QualityTab data={project.quality} onGenerate={() => runAI(aiAPI.analyzeQuality, 'quality')} loading={aiLoading} />;
      case 'maintenance': return (
        <MaintenanceTab
          data={project.maintenance}
          onUpdate={(val) => handleFieldUpdate('maintenance', val)}
          onGenerate={() => runAI(aiAPI.predictMaintenance, 'maintenance')}
          loading={aiLoading}
          saving={fieldSaving.maintenance}
        />
      );
      case 'kpis': return <KPIsTab data={project.kpis} onGenerate={() => runAI(aiAPI.generateKPIs, 'kpis')} loading={aiLoading} />;
      case 'chat': return <Chatbot projectId={parseInt(id)} onProjectUpdate={loadProject} />;
      default: return null;
    }
  };

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to={`/?view=${backView}`} className="p-2 hover:bg-gray-100 rounded-lg transition-colors"><ArrowLeft className="w-5 h-5" /></Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-500 text-sm mt-0.5">{project.description?.substring(0, 100)}</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadReport}
            disabled={downloadingReport}
            className="btn-secondary flex items-center gap-2 text-sm whitespace-nowrap"
            title="Download complete project report as PowerPoint"
          >
            <Download className="w-4 h-4" />
            {downloadingReport ? 'Generating...' : 'Download PPT Report'}
          </button>
          <StatusBadge status={project.status} />
          <div className="text-right">
            <p className="text-sm text-gray-500">Health Score</p>
            <p className={`text-lg font-bold ${project.health_score >= 80 ? 'text-accent-600' : project.health_score >= 60 ? 'text-warning-600' : 'text-danger-600'}`}>{project.health_score}%</p>
          </div>
        </div>
      </div>

      <div className="border-b border-gray-200 mb-6 overflow-x-auto">
        <nav className="flex gap-1 min-w-max">
          {tabs.map(({ id: tabId, label, icon: Icon }) => (
            <button
              key={tabId}
              onClick={() => navigate(`/project/${id}/${tabId}`)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                tab === tabId ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {aiError && (
        <div className="mb-4 bg-danger-50 border border-danger-500/20 text-danger-600 px-4 py-3 rounded-lg text-sm flex items-center justify-between">
          <span>{aiError}</span>
          <button onClick={() => setAiError('')} className="text-danger-400 hover:text-danger-600 ml-4">✕</button>
        </div>
      )}

      {renderTab()}

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md">
            <h2 className="text-xl font-bold mb-2">Delete Project</h2>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete <strong>{project.name}</strong>? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button onClick={handleDelete} disabled={deleting} className="flex-1 bg-danger-500 text-white px-4 py-2 rounded-lg hover:bg-danger-600 transition-colors font-medium disabled:opacity-50">
                {deleting ? 'Deleting...' : 'Delete Project'}
              </button>
              <button onClick={() => setShowDeleteConfirm(false)} className="btn-secondary flex-1">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function OverviewTab({ project, editForm, setEditForm, onSave, saving, onDelete }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Project Details</h3>
          <button onClick={onSave} disabled={saving} className="btn-primary flex items-center gap-2 text-sm">
            <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1">Project Name</label>
            <input className="input-field" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea className="input-field" rows={3} value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select className="input-field" value={editForm.status} onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}>
              <option value="planning">Planning</option>
              <option value="in_progress">In Progress</option>
              <option value="on_hold">On Hold</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Priority</label>
            <select className="input-field" value={editForm.priority} onChange={(e) => setEditForm({ ...editForm, priority: e.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Budget ($)</label>
            <input type="number" className="input-field" value={editForm.budget} onChange={(e) => setEditForm({ ...editForm, budget: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Actual Cost ($)</label>
            <input type="number" className="input-field" value={editForm.actual_cost} onChange={(e) => setEditForm({ ...editForm, actual_cost: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Start Date</label>
            <input type="date" className="input-field" value={editForm.start_date} onChange={(e) => setEditForm({ ...editForm, start_date: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">End Date</label>
            <input type="date" className="input-field" value={editForm.end_date} onChange={(e) => setEditForm({ ...editForm, end_date: e.target.value })} />
          </div>
        </div>
      </div>
      <div className="space-y-4">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Budget Utilization</h3>
          <p className="text-2xl font-bold">{formatCurrency(project.actual_cost)}</p>
          <p className="text-sm text-gray-500">of {formatCurrency(project.budget)}</p>
          <div className="mt-3"><ProgressBar value={(project.actual_cost / project.budget) * 100} /></div>
        </div>
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Project Health</h3>
          <div className="flex items-center gap-3">
            <div className={`text-3xl font-bold ${project.health_score >= 80 ? 'text-accent-600' : project.health_score >= 60 ? 'text-warning-600' : 'text-danger-600'}`}>
              {project.health_score}%
            </div>
            <ProgressBar value={project.health_score} color={project.health_score >= 80 ? 'bg-accent-500' : project.health_score >= 60 ? 'bg-warning-500' : 'bg-danger-500'} />
          </div>
        </div>
        <div className="card border border-danger-500/20">
          <p className="text-sm text-gray-500 mb-3">Permanently remove this project and all associated data.</p>
          <button onClick={onDelete} className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-danger-500/30 text-danger-600 rounded-lg hover:bg-danger-50 transition-colors text-sm font-medium">
            <Trash2 className="w-4 h-4" /> Delete Project
          </button>
        </div>
      </div>
    </div>
  );
}

function BudgetTab({ data, project, onGenerate, loading }) {
  if (!data || !data.categories) {
    return <EmptyState message="No budget analysis available yet." action={<AIGenerateButton onClick={onGenerate} loading={loading} label="Analyze Budget" />} />;
  }
  return (
    <div className="space-y-6">
      <div className="flex justify-end"><AIGenerateButton onClick={onGenerate} loading={loading} label="Refresh Analysis" /></div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card"><p className="text-sm text-gray-500">Planned</p><p className="text-xl font-bold">{formatCurrency(data.planned_budget)}</p></div>
        <div className="card"><p className="text-sm text-gray-500">Actual</p><p className="text-xl font-bold">{formatCurrency(data.actual_cost)}</p></div>
        <div className="card"><p className="text-sm text-gray-500">Variance</p><p className={`text-xl font-bold ${data.variance < 0 ? 'text-accent-600' : 'text-danger-600'}`}>{formatCurrency(data.variance)}</p></div>
        <div className="card"><p className="text-sm text-gray-500">Forecast</p><p className="text-xl font-bold">{formatCurrency(data.forecast?.estimated_final_cost)}</p></div>
      </div>
      <DataCard title="Cost Breakdown">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.categories}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
            <Tooltip formatter={(v) => formatCurrency(v)} /><Bar dataKey="planned" fill="#93c5fd" name="Planned" /><Bar dataKey="actual" fill="#3b82f6" name="Actual" />
          </BarChart>
        </ResponsiveContainer>
      </DataCard>
    </div>
  );
}

function QualityTab({ data, onGenerate, loading }) {
  if (!data || !data.inspections) {
    return <EmptyState message="No quality analysis available yet." action={<AIGenerateButton onClick={onGenerate} loading={loading} label="Analyze Quality" />} />;
  }
  return (
    <div className="space-y-6">
      <div className="flex justify-end"><AIGenerateButton onClick={onGenerate} loading={loading} label="Refresh Quality Data" /></div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card"><p className="text-sm text-gray-500">Defect Rate</p><p className="text-2xl font-bold">{data.defect_rate}%</p><p className="text-xs text-gray-400">Target: {data.target_defect_rate}%</p></div>
        <div className="card"><p className="text-sm text-gray-500">Quality Score</p><p className="text-2xl font-bold">{data.quality_score}/100</p></div>
        <div className="card"><p className="text-sm text-gray-500">Open CAPAs</p><p className="text-2xl font-bold">{data.capa_records?.filter(c => c.status !== 'completed').length || 0}</p></div>
      </div>
      <DataCard title="CAPA Records">
        {data.capa_records?.map((capa) => (
          <div key={capa.id} className="border-b border-gray-100 py-3 last:border-0">
            <div className="flex justify-between"><span className="font-medium">{capa.id}: {capa.issue}</span><StatusBadge status={capa.status} /></div>
            <p className="text-sm text-gray-600 mt-1">Root Cause: {capa.root_cause}</p>
            <p className="text-sm text-gray-600">Action: {capa.action}</p>
          </div>
        ))}
      </DataCard>
    </div>
  );
}

function KPIsTab({ data, onGenerate, loading }) {
  if (!data || !data.schedule_performance) {
    return <EmptyState message="No KPI dashboard data available yet." action={<AIGenerateButton onClick={onGenerate} loading={loading} label="Generate KPI Dashboard" />} />;
  }
  const radarData = [
    { metric: 'Schedule', value: (data.schedule_performance?.spi || 0) * 100 },
    { metric: 'Cost', value: (data.cost_performance?.cpi || 0) * 100 },
    { metric: 'Quality', value: data.quality_metrics?.first_pass_yield || 0 },
    { metric: 'Resources', value: data.resource_utilization?.overall || 0 },
    { metric: 'Health', value: data.project_health?.score || 0 },
  ];
  return (
    <div className="space-y-6">
      <div className="flex justify-end"><AIGenerateButton onClick={onGenerate} loading={loading} label="Refresh KPIs" /></div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="card text-center"><p className="text-xs text-gray-500">SPI</p><p className="text-2xl font-bold">{data.schedule_performance.spi}</p></div>
        <div className="card text-center"><p className="text-xs text-gray-500">CPI</p><p className="text-2xl font-bold">{data.cost_performance.cpi}</p></div>
        <div className="card text-center"><p className="text-xs text-gray-500">Defect Rate</p><p className="text-2xl font-bold">{data.quality_metrics.defect_rate}%</p></div>
        <div className="card text-center"><p className="text-xs text-gray-500">Utilization</p><p className="text-2xl font-bold">{data.resource_utilization.overall}%</p></div>
        <div className="card text-center"><p className="text-xs text-gray-500">Health</p><p className="text-2xl font-bold">{data.project_health.score}%</p></div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DataCard title="Performance Radar">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}><PolarGrid /><PolarAngleAxis dataKey="metric" /><PolarRadiusAxis domain={[0, 100]} /><Radar dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} /></RadarChart>
          </ResponsiveContainer>
        </DataCard>
        <DataCard title="Milestone Progress">
          <div className="space-y-4">
            <div><p className="text-sm text-gray-500">Completed</p><p className="text-3xl font-bold">{data.milestones.completed}/{data.milestones.total}</p></div>
            <ProgressBar value={(data.milestones.completed / data.milestones.total) * 100} />
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="bg-accent-50 p-3 rounded-lg"><p className="text-accent-600 font-medium">On Track</p><p className="text-2xl font-bold text-accent-700">{data.milestones.on_track}</p></div>
              <div className="bg-danger-50 p-3 rounded-lg"><p className="text-danger-600 font-medium">Delayed</p><p className="text-2xl font-bold text-danger-700">{data.milestones.delayed}</p></div>
            </div>
          </div>
        </DataCard>
      </div>
    </div>
  );
}
