import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '../api';
import { Loader2, AlertCircle } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar,
} from 'recharts';

export default function AnalyticsPage() {
  const { data: dashboard, isLoading: loadingDash, isError: errDash } = useQuery({
    queryKey: ['analytics', 'dashboard'],
    queryFn: () => analyticsAPI.dashboard().then(r => r.data),
  });

  const { data: trends, isLoading: loadingTrends } = useQuery({
    queryKey: ['analytics', 'trends'],
    queryFn: () => analyticsAPI.trends().then(r => r.data),
  });

  const { data: coverage, isLoading: loadingCov } = useQuery({
    queryKey: ['analytics', 'coverage'],
    queryFn: () => analyticsAPI.coverage().then(r => r.data),
  });

  const isLoading = loadingDash || loadingTrends || loadingCov;
  const isError = errDash;

  if (isLoading) {
    return (
      <AppLayout title="Analytics">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh', gap: 12 }}>
          <Loader2 size={24} className="animate-spin text-[var(--color-primary)]" />
          <span className="text-muted">Loading analytics data…</span>
        </div>
      </AppLayout>
    );
  }

  if (isError) {
    return (
      <AppLayout title="Analytics">
        <div className="card m-6" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 24, color: 'var(--color-danger)' }}>
          <AlertCircle size={22} />
          <span>Failed to load analytics data. Is the backend running?</span>
        </div>
      </AppLayout>
    );
  }

  const mappedTrends = trends?.map(t => {
    const total = t.passed + t.failed;
    return {
      date: t.date,
      passRate: total > 0 ? Math.round((t.passed / total) * 100) : 0,
    };
  }) || [];

  const mappedRadar = coverage?.map(c => ({
    subject: c.project_name.length > 10 ? c.project_name.substring(0, 10) + '...' : c.project_name,
    score: Math.round(c.coverage_pct),
  })) || [];

  return (
    <AppLayout title="Analytics">
      <div className="page-header">
        <div className="page-header-text">
          <h1>Analytics</h1>
          <p>Deep-dive into test coverage, trends, and API health</p>
        </div>
        <button className="btn btn-secondary" id="export-analytics-btn">Export CSV</button>
      </div>

      {/* Top stats */}
      <div className="grid-4" style={{ marginBottom: 32 }}>
        {[
          { label: 'Total Projects', value: dashboard?.total_projects || 0, pct: dashboard?.total_projects ? 100 : 0 },
          { label: 'Avg Pass Rate',  value: `${Math.round(dashboard?.pass_rate || 0)}%`, pct: dashboard?.pass_rate || 0 },
          { label: 'Avg Response Time', value: `${Math.round(dashboard?.avg_latency_ms || 0)}ms`, pct: Math.max(0, 100 - (dashboard?.avg_latency_ms || 0)/10) },
          { label: 'Runs This Month', value: `${dashboard?.runs_this_month || 0} / ${dashboard?.plan_limit || 0}`, pct: ((dashboard?.runs_this_month || 0) / (dashboard?.plan_limit || 1)) * 100 },
        ].map(({ label, value, pct }) => (
          <div key={label} className="stat-card">
            <div className="stat-card-label">{label}</div>
            <div className="stat-card-value">{value}</div>
            <div className="progress-bar-track" style={{ marginTop: 8 }}>
              <div className="progress-bar-fill" style={{ width: `${Math.min(100, pct)}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: 32 }}>
        {/* Pass Rate Trend */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ fontSize: '1rem' }}>Pass Rate Trend (Last 30 Days)</h3>
          </div>
          <div className="card-body" style={{ paddingTop: 8 }}>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={mappedTrends} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <Tooltip formatter={(v) => [`${v}%`, 'Pass Rate']}
                  contentStyle={{ borderRadius: 10, border: '1px solid var(--color-border)', fontSize: 12 }} />
                <Line type="monotone" dataKey="passRate" stroke="var(--color-primary)"
                  strokeWidth={2.5} dot={{ fill: 'var(--color-primary)', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* API Coverage Radar */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ fontSize: '1rem' }}>Coverage by Project</h3>
          </div>
          <div className="card-body" style={{ paddingTop: 8 }}>
            {mappedRadar.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={mappedRadar}>
                  <PolarGrid stroke="var(--color-border-light)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                  <Radar dataKey="score" stroke="var(--color-primary)" fill="var(--color-primary)" fillOpacity={0.15} />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-sm text-[var(--color-text-muted)] pb-12">
                No coverage data available
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Endpoint Coverage Heatmap */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ fontSize: '1rem' }}>Project API Coverage Breakdown</h3>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Endpoints Tested</th>
                <th>Untested</th>
                <th>Total Endpoints</th>
                <th>Coverage</th>
              </tr>
            </thead>
            <tbody>
              {coverage?.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center p-4 text-[var(--color-text-muted)]">No projects found</td>
                </tr>
              )}
              {coverage?.map(row => {
                const untested = row.endpoints_total - row.endpoints_tested;
                const pct = Math.round(row.coverage_pct);
                const healthy = pct >= 80;
                return (
                  <tr key={row.project_id}>
                    <td className="font-medium">{row.project_name}</td>
                    <td style={{ color: 'var(--color-success)', fontWeight: 600 }}>{row.endpoints_tested}</td>
                    <td style={{ color: untested > 0 ? 'var(--color-danger)' : 'var(--color-success)', fontWeight: 600 }}>
                      {untested}
                    </td>
                    <td>{row.endpoints_total}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="progress-bar-track" style={{ width: 100 }}>
                          <div className="progress-bar-fill" style={{
                            width: `${pct}%`,
                            background: healthy ? 'var(--color-success)' : 'var(--color-danger)',
                          }} />
                        </div>
                        <span className={`text-sm font-semibold`}
                          style={{ color: healthy ? 'var(--color-success)' : 'var(--color-danger)' }}>
                          {pct}%
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}
