// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  plan: 'free' | 'pro' | 'enterprise';
  monthly_run_count: number;
  created_at: string;
  updated_at: string;
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
  description?: string | null;
  openapi_spec?: Record<string, unknown> | null;
  owner_id: string;
  org_id?: string | null;
  created_at: string;
  updated_at: string;
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
  started_at?: string | null;
  completed_at?: string | null;
  // Aggregated counts (returned by the backend route)
  total_cases?: number | null;
  passed_cases?: number | null;
  failed_cases?: number | null;
}

export interface TestRunCreate {
  base_url: string;
  types?: Array<'functional' | 'edge' | 'security' | 'ai'>;
  enable_ai?: boolean;
}

export interface TestRunProgress {
  status: TestRunStatus;
  total_cases?: number | null;
  completed_cases?: number | null;
  passed_cases?: number | null;
  failed_cases?: number | null;
  progress_pct?: number | null;
}

// ── Test Results ──────────────────────────────────────────────────────────────
export interface TestResult {
  id: string;
  test_run_id: string;
  test_case_id: string;
  passed: boolean;
  status: string;
  actual_status_code?: number | null;
  latency_ms: number;
  response_time_ms: number;
  ai_failure_analysis?: Record<string, unknown> | null;
}

// ── Analytics ─────────────────────────────────────────────────────────────────
export interface DashboardStats {
  total_projects: number;
  total_runs: number;
  pass_rate: number;         // 0.0 – 100.0
  avg_latency_ms: number;
  runs_this_month: number;
  plan_limit: number;
}

export interface TrendPoint {
  date: string;
  passed: number;
  failed: number;
}

export interface CoverageProject {
  project_id: string;
  project_name: string;
  endpoints_total: number;
  endpoints_tested: number;
  coverage_pct: number;
}


export interface AIInsightResponse {
  id: string;
  run_id: string;
  endpoint: string;
  root_cause: string;
  suggested_fix: string;
  confidence: number;
  security_score: number;
  owasp_issues: OWASPIssue[];
  created_at: string;
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

// ── Organizations ─────────────────────────────────────────────────────────────
export interface Organization {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  member_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface OrgCreate {
  name: string;
}

export interface OrgUpdate {
  name?: string;
}

export interface OrgMemberAdd {
  user_id: string;
}
