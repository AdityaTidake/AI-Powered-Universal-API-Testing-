import apiClient from './client';
import type {
  AuthTokens, LoginRequest, RegisterRequest, User,
  Project, ProjectCreate,
  TestRun, TestRunCreate, TestRunProgress, TestResult,
  DashboardStats, TrendPoint, CoverageProject, AIInsightResponse,
  Organization, OrgCreate, OrgUpdate, OrgMemberAdd,
} from '../types';

// ── Auth API ──────────────────────────────────────────────────────────────────
export const authAPI = {
  login:   (data: LoginRequest)   => apiClient.post<AuthTokens>('/api/v1/auth/login', data),
  register:(data: RegisterRequest) => apiClient.post<AuthTokens>('/api/v1/auth/register', data),
  me:      ()                     => apiClient.get<User>('/api/v1/auth/me'),
  logout:  ()                     => apiClient.post('/api/v1/auth/logout'),
  refresh: (refresh_token: string) =>
    apiClient.post<AuthTokens>('/api/v1/auth/refresh', { refresh_token }),
};

// ── Organizations API ─────────────────────────────────────────────────────────
export const orgsAPI = {
  list:         () => apiClient.get<Organization[]>('/api/v1/orgs'),
  get:          (id: string) => apiClient.get<Organization>(`/api/v1/orgs/${id}`),
  create:       (data: OrgCreate) => apiClient.post<Organization>('/api/v1/orgs', data),
  update:       (id: string, data: OrgUpdate) => apiClient.patch<Organization>(`/api/v1/orgs/${id}`, data),
  delete:       (id: string) => apiClient.delete(`/api/v1/orgs/${id}`),
  addMember:    (id: string, data: OrgMemberAdd) => apiClient.post<Organization>(`/api/v1/orgs/${id}/members`, data),
  removeMember: (id: string, userId: string) => apiClient.delete<Organization>(`/api/v1/orgs/${id}/members/${userId}`),
  listProjects: (id: string) => apiClient.get<Project[]>(`/api/v1/orgs/${id}/projects`),
};

// ── Projects API ──────────────────────────────────────────────────────────────
export const projectsAPI = {
  list:      ()                       => apiClient.get<Project[]>('/api/v1/projects'),
  get:       (id: string)             => apiClient.get<Project>(`/api/v1/projects/${id}`),
  create:    (data: ProjectCreate)    => apiClient.post<Project>('/api/v1/projects', data),
  delete:    (id: string)             => apiClient.delete(`/api/v1/projects/${id}`),
  uploadSpec:(id: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return apiClient.post<Project>(`/api/v1/projects/${id}/upload-spec`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const testRunsAPI = {
  create:  (projectId: string, data: TestRunCreate) =>
    apiClient.post<TestRun>(`/api/v1/projects/${projectId}/runs`, data),
  list:    (projectId: string) =>
    apiClient.get<TestRun[]>(`/api/v1/projects/${projectId}/runs`),
  get:     (runId: string)     => apiClient.get<TestRun>(`/api/v1/runs/${runId}`),
  status:  (runId: string)     => apiClient.get<TestRunProgress>(`/api/v1/runs/${runId}/status`),
  results: (runId: string)     => apiClient.get<TestResult[]>(`/api/v1/runs/${runId}/results`),
  delete:  (runId: string)     => apiClient.delete(`/api/v1/runs/${runId}`),
  cancel:           (runId: string) => apiClient.patch(`/api/v1/runs/${runId}/cancel`),
  exportReportHtml: (runId: string) => apiClient.get(`/api/v1/runs/${runId}/report/html`, { responseType: 'blob' }),
  exportReportJson: (runId: string) => apiClient.get(`/api/v1/runs/${runId}/report/json`, { responseType: 'blob' }),
};

// ── Analytics API ─────────────────────────────────────────────────────────────
export const analyticsAPI = {
  dashboard: () => apiClient.get<DashboardStats>('/api/v1/analytics/dashboard'),
  trends:    () => apiClient.get<TrendPoint[]>('/api/v1/analytics/trends'),
  coverage:  () => apiClient.get<CoverageProject[]>('/api/v1/analytics/coverage'),
  insights:  () => apiClient.get<AIInsightResponse[]>('/api/v1/analytics/insights'),
};
