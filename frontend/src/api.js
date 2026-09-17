import axios from 'axios';
import { log } from './utils/logger';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    log.apiError(`${error.config?.method?.toUpperCase()} ${error.config?.url}`, error);
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

export const projectsAPI = {
  list: () => api.get('/projects/'),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects/', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  listTasks: (projectId) => api.get(`/projects/${projectId}/tasks`),
  createTask: (projectId, data) => api.post(`/projects/${projectId}/tasks`, data),
  updateTask: (projectId, taskId, data) => api.put(`/projects/${projectId}/tasks/${taskId}`, data),
  deleteTask: (projectId, taskId) => api.delete(`/projects/${projectId}/tasks/${taskId}`),
  downloadReportPptx: (projectId) =>
    api.get(`/projects/${projectId}/report/pptx`, { responseType: 'blob' }),
  updateGanttTask: (projectId, data) => api.patch(`/projects/${projectId}/gantt/task`, data),
  syncProject: (projectId) => api.post(`/projects/${projectId}/sync`),
};

export const aiAPI = {
  chat: (message, projectId) => api.post('/ai/chat', { message, project_id: projectId }),
  chatHistory: (projectId) => api.get(`/ai/chat/${projectId}/history`),
  generateCharter: (projectId, prompt) => api.post(`/ai/charter/${projectId}`, { project_id: projectId, prompt }),
  generateWBS: (projectId, prompt) => api.post(`/ai/wbs/${projectId}`, { project_id: projectId, prompt }),
  generateGantt: (projectId, prompt) => api.post(`/ai/gantt/${projectId}`, { project_id: projectId, prompt }),
  optimizeResources: (projectId, prompt) => api.post(`/ai/resources/${projectId}`, { project_id: projectId, prompt }),
  analyzeBudget: (projectId, prompt) => api.post(`/ai/budget/${projectId}`, { project_id: projectId, prompt }),
  planInventory: (projectId, prompt) => api.post(`/ai/inventory/${projectId}`, { project_id: projectId, prompt }),
  analyzeRisks: (projectId, prompt) => api.post(`/ai/risks/${projectId}`, { project_id: projectId, prompt }),
  analyzeQuality: (projectId, prompt) => api.post(`/ai/quality/${projectId}`, { project_id: projectId, prompt }),
  predictMaintenance: (projectId, prompt) => api.post(`/ai/maintenance/${projectId}`, { project_id: projectId, prompt }),
  generateKPIs: (projectId, prompt) => api.post(`/ai/kpis/${projectId}`, { project_id: projectId, prompt }),
};

export default api;
