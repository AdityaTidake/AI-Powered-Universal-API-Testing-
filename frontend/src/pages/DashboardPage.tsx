/**
 * DashboardPage — live stats, charts, and recent runs from the API.
 * Falls back to skeleton loading states while fetching.
 */
import AppLayout from '../components/AppLayout';
import {
  Activity, CheckCircle, Clock, FolderOpen, Play, AlertTriangle, Loader2,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend,
} from 'recharts';
import { useDashboardStats, useTrends } from '../store/analyticsStore';
import { useProjects } from '../store/projectsStore';
import { useTestRuns } from '../store/testRunsStore';
import type { TestRunStatus } from '../types';

// ── Skeleton block ─────────────────────────────────────────────────────────────
function Skeleton({ width, height }: { width?: number | string; height?: number | string }) {
  return (
    <div style={{
      width: width ?? '100%', height: height ?? 20,
      background: 'var(--color-surface-alt)',
      borderRadius: 6,
      animation: 'pulse 1.6s ease infinite',
    }} />
  );
}

// ── Status badge ───────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: TestRunStatus }) {
  const map: Record<string, string> = {
    COMPLETED: 'badge-success', FAILED: 'badge-danger',
    RUNNING: 'badge-info',      PENDING: 'badge-gray',
  };
  return <span className={`badge ${map[status] ?? 'badge-gray'}`}>{status}</span>;
}

// ── Recent runs across all projects ───────────────────────────────────────────
function RecentRunsSection() {
  const { data: projects } = useProjects();

  // Pull runs from the first 4 projects and merge
  const runsQueries = [0, 1, 2, 3].map(i => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const p = projects?.[i];
    // eslint-disable-next-line react-hooks/rules-of-hooks
    return useTestRuns(p?.id);
  });

  const allRuns = runsQueries
    .flatMap((q, i) =>
      (q.data ?? []).map(r => ({
        ...r,
        projectName: projects?.[i]?.name ?? 'Unknown',
      }))
    )
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 8);

  const isLoading = runsQueries.some(q => q.isLoading);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 16 }}>
        {[1, 2, 3].map(i => <Skeleton key={i} height={36} />)}
      </div>
    );
  }

  if (allRuns.length === 0) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No test runs yet. Go to Projects to launch your first run.
      </div>
    );
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Project</th>
            <th>Status</th>
            <th>Tests</th>
            <th>Pass Rate</th>
            <th>When</th>
          </tr>
        </thead>
        <tbody>
          {allRuns.map(run => {
            const passRate = run.total_cases
              ? Math.round(((run.passed_cases ?? 0) / run.total_cases) * 100)
              : null;
            return (
              <tr key={run.id}>
                <td><span className="font-medium">{run.projectName}</span></td>
                <td><StatusBadge status={run.status} /></td>
                <td>{run.total_cases ?? '--'}</td>
                <td>
                  {passRate !== null
                    ? (
                      <div className="flex items-center gap-2">
                        <div className="progress-bar-track" style={{ width: 80 }}>
                          <div className="progress-bar-fill" style={{ width: `${passRate}%` }} />
                        </div>
                        <span className="text-sm">{passRate}%</span>
                      </div>
                    )
                    : '--'}
                </td>
                <td className="text-muted text-sm">
                  {new Date(run.created_at).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── Main ───────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { data: stats, isLoading: loadingStats } = useDashboardStats();
  const { data: trends, isLoading: loadingTrends } = useTrends();

  const statCards = [
    {
      label: 'Total Test Runs',
      value: loadingStats ? null : stats?.total_runs.toLocaleString() ?? '—',
      icon: Play,
      iconBg: 'var(--color-primary-muted)',
      iconColor: 'var(--color-primary)',
    },
    {
      label: 'Pass Rate',
      value: loadingStats ? null : stats != null ? `${stats.pass_rate}%` : '—',
      icon: CheckCircle,
      iconBg: 'var(--color-success-bg)',
      iconColor: 'var(--color-success)',
    },
    {
      label: 'Avg Latency',
      value: loadingStats ? null : stats != null ? `${stats.avg_latency_ms}ms` : '—',
      icon: Clock,
      iconBg: 'var(--color-info-bg)',
      iconColor: 'var(--color-info)',
    },
    {
      label: 'Active Projects',
      value: loadingStats ? null : stats?.total_projects.toLocaleString() ?? '—',
      icon: FolderOpen,
      iconBg: 'var(--color-warning-bg)',
      iconColor: 'var(--color-warning)',
    },
  ];

  const trendData = trends ?? [];

  return (
    <AppLayout title="Dashboard">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-text">
          <h1>Overview</h1>
          <p>Monitor your API testing health at a glance</p>
        </div>
        <a href="/projects" className="btn btn-primary">
          <Play size={16} />
          New Test Run
        </a>
      </div>

      {/* Stat Cards */}
      <div className="grid-4" style={{ marginBottom: 32 }}>
        {statCards.map(({ label, value, icon: Icon, iconBg, iconColor }) => (
          <div key={label} className="stat-card">
            <div className="stat-card-header">
              <div>
                <div className="stat-card-label">{label}</div>
                <div className="stat-card-value" style={{ marginTop: 8 }}>
                  {value === null
                    ? <Skeleton width={80} height={28} />
                    : value}
                </div>
              </div>
              <div className="stat-card-icon" style={{ background: iconBg }}>
                <Icon size={22} style={{ color: iconColor }} />
              </div>
            </div>
            <div>
              {loadingStats
                ? <Skeleton width={120} height={14} />
                : (
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {stats?.runs_this_month ?? 0} / {stats?.plan_limit ?? '—'} runs this month
                  </span>
                )}
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: 32 }}>
        {/* Pass/Fail Trend */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 style={{ fontSize: '1rem' }}>Pass / Fail Trend</h3>
              <p className="text-sm text-muted" style={{ marginTop: 2 }}>Last 14 days</p>
            </div>
            <Activity size={18} style={{ color: 'var(--color-primary)' }} />
          </div>
          <div className="card-body" style={{ paddingTop: 8 }}>
            {loadingTrends
              ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 220 }}>
                  <Loader2 size={28} style={{ color: 'var(--color-primary)', animation: 'spin 1s linear infinite' }} />
                </div>
              )
              : (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={trendData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="passGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="var(--color-success)" stopOpacity={0.18} />
                        <stop offset="95%" stopColor="var(--color-success)" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="failGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="var(--color-danger)" stopOpacity={0.18} />
                        <stop offset="95%" stopColor="var(--color-danger)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                    <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                    <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid var(--color-border)', fontSize: 12 }} />
                    <Area type="monotone" dataKey="passed" name="Passed" stroke="var(--color-success)"
                      fill="url(#passGrad)" strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="failed" name="Failed" stroke="var(--color-danger)"
                      fill="url(#failGrad)" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
          </div>
        </div>

        {/* Weekly Bar Chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 style={{ fontSize: '1rem' }}>Weekly Test Volume</h3>
              <p className="text-sm text-muted" style={{ marginTop: 2 }}>Passed vs failed by day</p>
            </div>
            <AlertTriangle size={18} style={{ color: 'var(--color-warning)' }} />
          </div>
          <div className="card-body" style={{ paddingTop: 8 }}>
            {loadingTrends
              ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 220 }}>
                  <Loader2 size={28} style={{ color: 'var(--color-primary)', animation: 'spin 1s linear infinite' }} />
                </div>
              )
              : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={trendData.slice(-7)} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                    <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                    <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid var(--color-border)', fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="passed" name="Passed" fill="var(--color-success)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="failed" name="Failed" fill="var(--color-danger)"  radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
          </div>
        </div>
      </div>

      {/* Recent Runs */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ fontSize: '1rem' }}>Recent Test Runs</h3>
          <a href="/runs" className="btn btn-ghost btn-sm">View all</a>
        </div>
        <RecentRunsSection />
      </div>
    </AppLayout>
  );
}
