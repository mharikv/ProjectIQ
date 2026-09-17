import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { projectsAPI } from '../api';
import { getApiErrorMessage } from '../utils/logger';
import { log } from '../utils/logger';
import {
  Plus, FolderKanban, Calendar, DollarSign, Activity, AlertTriangle,
  Trash2, PlayCircle, CheckCircle2, Clock,
} from 'lucide-react';

const IN_PROGRESS_STATUSES = ['planning', 'in_progress', 'on_hold'];
const COMPLETED_STATUSES = ['completed', 'cancelled'];

const statusColors = {
  planning: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-accent-100 text-accent-700',
  on_hold: 'bg-warning-50 text-warning-600',
  completed: 'bg-gray-100 text-gray-700',
  cancelled: 'bg-danger-50 text-danger-600',
};

const priorityColors = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-warning-50 text-warning-600',
  critical: 'bg-danger-50 text-danger-600',
};

export default function Dashboard() {
  const [searchParams] = useSearchParams();
  const view = searchParams.get('view') || 'in_progress';
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [createError, setCreateError] = useState('');
  const [form, setForm] = useState({ name: '', description: '', budget: '', priority: 'medium', start_date: '', end_date: '' });

  useEffect(() => { loadProjects(); }, []);

  const loadProjects = async () => {
    try {
      const { data } = await projectsAPI.list();
      setProjects(data);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredProjects = projects.filter((p) =>
    view === 'completed'
      ? COMPLETED_STATUSES.includes(p.status)
      : IN_PROGRESS_STATUSES.includes(p.status)
  );

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateError('');
    try {
      log.info('Creating project:', form.name);
      await projectsAPI.create({
        ...form,
        budget: parseFloat(form.budget) || 0,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
      });
      setShowCreate(false);
      setForm({ name: '', description: '', budget: '', priority: 'medium', start_date: '', end_date: '' });
      loadProjects();
    } catch (err) {
      setCreateError(getApiErrorMessage(err, 'Failed to create project'));
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await projectsAPI.delete(deleteTarget.id);
      setDeleteTarget(null);
      loadProjects();
    } catch {
      alert('Failed to delete project');
    } finally {
      setDeleting(false);
    }
  };

  const formatCurrency = (val) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

  const isCompletedView = view === 'completed';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            {isCompletedView ? (
              <CheckCircle2 className="w-7 h-7 text-gray-500" />
            ) : (
              <PlayCircle className="w-7 h-7 text-primary-600" />
            )}
            <h1 className="text-2xl font-bold text-gray-900">
              {isCompletedView ? 'Completed Projects' : 'In Progress Projects'}
            </h1>
          </div>
          <p className="text-gray-500 mt-1">
            {isCompletedView
              ? 'Finished and closed manufacturing projects'
              : 'Active projects currently in planning or execution'}
          </p>
        </div>
        {!isCompletedView && (
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Project
          </button>
        )}
      </div>

      <div className="flex gap-2 mb-8">
        <Link
          to="/?view=in_progress"
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            !isCompletedView ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <PlayCircle className="w-4 h-4" />
          In Progress ({projects.filter((p) => IN_PROGRESS_STATUSES.includes(p.status)).length})
        </Link>
        <Link
          to="/?view=completed"
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            isCompletedView ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          Completed ({projects.filter((p) => COMPLETED_STATUSES.includes(p.status)).length})
        </Link>
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-lg">
            <h2 className="text-xl font-bold mb-4">Create New Project</h2>
            {createError && (
              <div className="bg-danger-50 border border-danger-500/20 text-danger-600 px-4 py-3 rounded-lg mb-4 text-sm">{createError}</div>
            )}
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Project Name</label>
                <input className="input-field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea className="input-field" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Budget ($)</label>
                  <input type="number" className="input-field" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Priority</label>
                  <select className="input-field" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Start Date</label>
                  <input type="date" className="input-field" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">End Date</label>
                  <input type="date" className="input-field" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary flex-1">Create Project</button>
                <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary flex-1">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md">
            <h2 className="text-xl font-bold mb-2">Delete Project</h2>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete <strong>{deleteTarget.name}</strong>? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button onClick={handleDelete} disabled={deleting} className="flex-1 bg-danger-500 text-white px-4 py-2 rounded-lg hover:bg-danger-600 transition-colors font-medium disabled:opacity-50">
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
              <button onClick={() => setDeleteTarget(null)} className="btn-secondary flex-1">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {filteredProjects.length === 0 ? (
        <div className={`card text-center py-16 ${isCompletedView ? 'bg-gray-50' : ''}`}>
          {isCompletedView ? (
            <CheckCircle2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          ) : (
            <FolderKanban className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          )}
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {isCompletedView ? 'No completed projects' : 'No in-progress projects'}
          </h3>
          <p className="text-gray-500 mb-6">
            {isCompletedView
              ? 'Projects marked as completed or cancelled will appear here'
              : 'Create a new project or mark an existing one as in progress'}
          </p>
          {!isCompletedView && (
            <button onClick={() => setShowCreate(true)} className="btn-primary">Create Project</button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredProjects.map((project) => {
            const isCompleted = COMPLETED_STATUSES.includes(project.status);
            return (
              <div
                key={project.id}
                className={`card hover:shadow-md transition-shadow group relative border-l-4 ${
                  isCompleted
                    ? 'border-l-gray-400 bg-gray-50/80'
                    : 'border-l-primary-500 bg-white'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <Link to={`/project/${project.id}`} className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {isCompleted ? (
                        <CheckCircle2 className="w-5 h-5 text-gray-400 shrink-0" />
                      ) : (
                        <Clock className="w-5 h-5 text-primary-500 shrink-0" />
                      )}
                      <h3 className={`text-lg font-semibold truncate group-hover:text-primary-600 transition-colors ${
                        isCompleted ? 'text-gray-700' : 'text-gray-900'
                      }`}>
                        {project.name}
                      </h3>
                    </div>
                  </Link>
                  <div className="flex items-center gap-2 ml-2 shrink-0">
                    <span className={`badge ${statusColors[project.status] || statusColors.planning}`}>
                      {project.status?.replace('_', ' ')}
                    </span>
                    <button
                      onClick={() => setDeleteTarget(project)}
                      className="p-1.5 text-gray-400 hover:text-danger-500 hover:bg-danger-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                      title="Delete project"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <Link to={`/project/${project.id}`}>
                  <p className={`text-sm mb-4 line-clamp-2 ${isCompleted ? 'text-gray-400' : 'text-gray-500'}`}>
                    {project.description}
                  </p>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <DollarSign className="w-4 h-4 text-gray-400" />
                      <span>{formatCurrency(project.budget)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Activity className="w-4 h-4 text-gray-400" />
                      <span>Health: {project.health_score}%</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`badge ${priorityColors[project.priority]}`}>{project.priority}</span>
                    </div>
                    {project.end_date && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span>{new Date(project.end_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                  {!isCompleted && project.health_score < 70 && (
                    <div className="mt-3 flex items-center gap-2 text-warning-600 text-sm">
                      <AlertTriangle className="w-4 h-4" />
                      <span>Needs attention</span>
                    </div>
                  )}
                  {isCompleted && (
                    <div className="mt-3 flex items-center gap-2 text-gray-500 text-sm">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Project closed</span>
                    </div>
                  )}
                </Link>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
