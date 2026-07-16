import AppLayout from '../components/AppLayout';
import {
  Activity, CheckCircle, Clock, TrendingUp, FolderOpen, Play, AlertTriangle,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend,
} from 'recharts';

// ── Mock data (replace with API calls in Phase 3) ─────────────────────────────
const TREND_DATA = [
  { date: 'Jul 1',  passed: 42, failed: 5  },
  { date: 'Jul 3',  passed: 58, failed: 8  },
  { date: 'Jul 5',  passed: 71, failed: 3  },
  { date: 'Jul 7',  passed: 65, failed: 12 },
  { date: 'Jul 9',  passed: 89, failed: 4  },
  { date: 'Jul 11', passed: 95, failed: 6  },
  { date: 'Jul 13', passed: 103, failed: 2 },
];

const RECENT_RUNS = [
  { id: '1', project: 'Payment API',    status: 'COMPLETED', tests: 84,  passed: 81, time: '2m 14s', ago: '10 min ago' },
  { id: '2', project: 'Auth Service',   status: 'FAILED',    tests: 32,  passed: 28, time: '45s',    ago: '1 hr ago'   },
  { id: '3', project: 'Product API',    status: 'COMPLETED', tests: 120, passed: 120,time: '4m 02s', ago: '3 hr ago'   },
  { id: '4', project: 'Notification API',status: 'RUNNING',  tests: 60,  passed: 34, time: '--',     ago: 'Just now'   },
];

const STAT_CARDS = [
  {
    label: 'Total Test Runs',
    value: '1,284',
    icon: Play,
    trend: '+12%',
    trendUp: true,
    iconBg: 'var(--color-primary-muted)',
    iconColor: 'var(--color-primary)',
  },
  {
    label: 'Pass Rate',
    value: '94.2%',
    icon: CheckCircle,
    trend: '+3.1%',
    trendUp: true,
    iconBg: 'var(--color-success-bg)',
    iconColor: 'var(--color-success)',
  },
  {
    label: 'Avg Latency',
    value: '148ms',
    icon: Clock,
    trend: '-12ms',
    trendUp: true,
    iconBg: 'var(--color-info-bg)',
    iconColor: 'var(--color-info)',
  },
  {
    label: 'Active Projects',
    value: '7',
    icon: FolderOpen,
    trend: '+2',
    trendUp: true,
    iconBg: 'var(--color-warning-bg)',
    iconColor: 'var(--color-warning)',
  },
];

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    COMPLETED: 'badge-success',
    FAILED: 'badge-danger',
    RUNNING: 'badge-info',
    PENDING: 'badge-gray',
  };
  return <span className={`badge ${map[status] ?? 'badge-gray'}`}>{status}</span>;
}

export default function DashboardPage() {
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
        {STAT_CARDS.map(({ label, value, icon: Icon, trend, trendUp, iconBg, iconColor }) => (
          <div key={label} className="stat-card">
            <div className="stat-card-header">
              <div>
                <div className="stat-card-label">{label}</div>
                <div className="stat-card-value" style={{ marginTop: 8 }}>{value}</div>
              </div>
              <div className="stat-card-icon" style={{ background: iconBg }}>
                <Icon size={22} style={{ color: iconColor }} />
              </div>
            </div>
            <div>
              <span className={`stat-card-trend ${trendUp ? 'trend-up' : 'trend-down'}`}>
                <TrendingUp size={11} />
                {trend}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginLeft: 8 }}>
                vs last month
              </span>
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
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={TREND_DATA} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
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
          </div>
        </div>

        {/* Weekly Bar */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 style={{ fontSize: '1rem' }}>Weekly Test Volume</h3>
              <p className="text-sm text-muted" style={{ marginTop: 2 }}>Passed vs failed by day</p>
            </div>
            <AlertTriangle size={18} style={{ color: 'var(--color-warning)' }} />
          </div>
          <div className="card-body" style={{ paddingTop: 8 }}>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={TREND_DATA} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid var(--color-border)', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="passed" name="Passed" fill="var(--color-success)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="failed" name="Failed" fill="var(--color-danger)"  radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Runs */}
      <div className="card">
        <div className="card-header">
          <h3 style={{ fontSize: '1rem' }}>Recent Test Runs</h3>
          <a href="/runs" className="btn btn-ghost btn-sm">View all</a>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Status</th>
                <th>Tests</th>
                <th>Pass Rate</th>
                <th>Duration</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {RECENT_RUNS.map(run => (
                <tr key={run.id}>
                  <td><span className="font-medium">{run.project}</span></td>
                  <td><StatusBadge status={run.status} /></td>
                  <td>{run.tests}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="progress-bar-track" style={{ width: 80 }}>
                        <div className="progress-bar-fill"
                          style={{ width: `${Math.round(run.passed / run.tests * 100)}%` }} />
                      </div>
                      <span className="text-sm">
                        {Math.round(run.passed / run.tests * 100)}%
                      </span>
                    </div>
                  </td>
                  <td><code>{run.time}</code></td>
                  <td className="text-muted text-sm">{run.ago}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}
