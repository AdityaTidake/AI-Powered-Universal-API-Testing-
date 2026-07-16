// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  plan: 'free' | 'pro' | 'enterprise';
  monthly_run_count: number;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  org_name?: string;
}

// ── Projects ──────────────────────────────────────────────────────────────────
export interface Project {
  id: string;
  name: string;
  description?: string;
  openapi_spec?: Record<string, unknown>;
  owner_id: string;
  created_at: string;
  updated_at: string;
  test_run_count?: number;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

// ── Test Runs ─────────────────────────────────────────────────────────────────
export type TestRunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface TestRun {
  id: string;
  project_id: string;
  base_url: string;
  status: TestRunStatus;
  created_at: string;
  updated_at: string;
}

export interface TestRunCreate {
  base_url: string;
  spec_path?: string;
  types?: string[];
  enable_ai?: boolean;
}

export interface TestRunProgress {
  status: TestRunStatus;
  completed: number;
  total: number;
  progress_pct: number;
}

// ── Test Results ──────────────────────────────────────────────────────────────
export interface TestResult {
  id: string;
  test_case_id: string;
  status: 'passed' | 'failed';
  response_time_ms: number;
  actual_status_code: number;
}

// ── Analytics ─────────────────────────────────────────────────────────────────
export interface DashboardStats {
  total_projects: number;
  total_runs: number;
  pass_rate: number;
  avg_latency_ms: number;
  runs_this_month: number;
  plan_limit: number;
}

export interface TrendPoint {
  date: string;
  passed: number;
  failed: number;
}

// ── AI Insights ───────────────────────────────────────────────────────────────
export interface AIAnalysis {
  run_id: string;
  root_cause: string;
  suggested_fix: string;
  confidence: number;
  security_score: number;
  owasp_issues: OWASPIssue[];
  similar_failures: SimilarFailure[];
}

export interface OWASPIssue {
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
}

export interface SimilarFailure {
  endpoint: string;
  error_type: string;
  fix_applied: string;
  similarity_score: number;
}

// ── API Error ─────────────────────────────────────────────────────────────────
export interface APIError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// ── Pagination ────────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
