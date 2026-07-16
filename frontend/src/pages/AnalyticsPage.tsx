import AppLayout from '../components/AppLayout';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar,
} from 'recharts';

const TREND = [
  { date: 'Jun 20', passRate: 88 }, { date: 'Jun 25', passRate: 91 },
  { date: 'Jul 1',  passRate: 87 }, { date: 'Jul 5',  passRate: 94 },
  { date: 'Jul 10', passRate: 96 }, { date: 'Jul 15', passRate: 94 },
  { date: 'Jul 16', passRate: 97 },
];

const COVERAGE = [
  { endpoint: 'POST /auth/login',    passed: 12, failed: 1 },
  { endpoint: 'GET /users/{id}',     passed: 9,  failed: 0 },
  { endpoint: 'POST /orders',        passed: 15, failed: 3 },
  { endpoint: 'GET /products',       passed: 20, failed: 0 },
  { endpoint: 'DELETE /orders/{id}', passed: 6,  failed: 2 },
  { endpoint: 'PATCH /users/{id}',   passed: 8,  failed: 1 },
];

const RADAR_DATA = [
  { subject: 'Auth',    score: 92 },
  { subject: 'Products',score: 88 },
  { subject: 'Orders',  score: 76 },
  { subject: 'Users',   score: 95 },
  { subject: 'Payments',score: 83 },
  { subject: 'Reports', score: 70 },
];

export default function AnalyticsPage() {
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
          { label: 'Endpoints Covered', value: '47 / 52',   pct: 90 },
          { label: '30-day Pass Rate',  value: '94.2%',     pct: 94 },
          { label: 'Avg Response Time', value: '148ms',     pct: 70 },
          { label: 'Security Score',    value: '78 / 100',  pct: 78 },
        ].map(({ label, value, pct }) => (
          <div key={label} className="stat-card">
            <div className="stat-card-label">{label}</div>
            <div className="stat-card-value">{value}</div>
            <div className="progress-bar-track" style={{ marginTop: 8 }}>
              <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: 32 }}>
        {/* Pass Rate Trend */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ fontSize: '1rem' }}>Pass Rate Trend</h3>
          </div>
          <div className="card-body" style={{ paddingTop: 8 }}>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={TREND} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <YAxis domain={[80, 100]} tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
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
            <h3 style={{ fontSize: '1rem' }}>Coverage by Domain</h3>
          </div>
          <div className="card-body" style={{ paddingTop: 8 }}>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={RADAR_DATA}>
                <PolarGrid stroke="var(--color-border-light)" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <Radar dataKey="score" stroke="var(--color-primary)" fill="var(--color-primary)" fillOpacity={0.15} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Endpoint Coverage Heatmap */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ fontSize: '1rem' }}>Endpoint Coverage Breakdown</h3>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Total</th>
                <th>Health</th>
              </tr>
            </thead>
            <tbody>
              {COVERAGE.map(row => {
                const total   = row.passed + row.failed;
                const pct     = Math.round((row.passed / total) * 100);
                const healthy = pct >= 90;
                return (
                  <tr key={row.endpoint}>
                    <td><code>{row.endpoint}</code></td>
                    <td style={{ color: 'var(--color-success)', fontWeight: 600 }}>{row.passed}</td>
                    <td style={{ color: row.failed ? 'var(--color-danger)' : 'var(--color-success)', fontWeight: 600 }}>
                      {row.failed}
                    </td>
                    <td>{total}</td>
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
