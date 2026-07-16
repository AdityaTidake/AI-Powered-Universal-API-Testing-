import AppLayout from '../components/AppLayout';
import { Play, Clock, CheckCircle2, XCircle, Loader } from 'lucide-react';

const MOCK_RUNS = [
  { id: '1', project: 'Payment API',     status: 'COMPLETED', total: 84,  passed: 81, failed: 3,  duration: '2m 14s', created: 'Jul 16, 10:30 AM' },
  { id: '2', project: 'Auth Service',    status: 'FAILED',    total: 32,  passed: 28, failed: 4,  duration: '45s',    created: 'Jul 16, 09:15 AM' },
  { id: '3', project: 'Product Catalog', status: 'RUNNING',   total: 60,  passed: 34, failed: 0,  duration: '--',     created: 'Jul 16, 11:00 AM' },
  { id: '4', project: 'Payment API',     status: 'COMPLETED', total: 120, passed: 120,failed: 0,  duration: '4m 02s', created: 'Jul 15, 06:00 PM' },
  { id: '5', project: 'Auth Service',    status: 'PENDING',   total: 0,   passed: 0,  failed: 0,  duration: '--',     created: 'Jul 15, 03:00 PM' },
];

function StatusIcon({ status }: { status: string }) {
  if (status === 'COMPLETED') return <CheckCircle2 size={16} style={{ color: 'var(--color-success)' }} />;
  if (status === 'FAILED')    return <XCircle      size={16} style={{ color: 'var(--color-danger)'  }} />;
  if (status === 'RUNNING')   return <Loader       size={16} style={{ color: 'var(--color-info)', animation: 'spin 1s linear infinite' }} />;
  return <Clock size={16} style={{ color: 'var(--color-text-muted)' }} />;
}

function StatusBadge({ status }: { status: string }) {
  const cls: Record<string, string> = {
    COMPLETED: 'badge-success', FAILED: 'badge-danger',
    RUNNING: 'badge-info',      PENDING: 'badge-gray',
  };
  return (
    <span className={`badge ${cls[status] ?? 'badge-gray'}`}>
      <StatusIcon status={status} />
      {status}
    </span>
  );
}

export default function TestRunsPage() {
  return (
    <AppLayout title="Test Runs">
      <div className="page-header">
        <div className="page-header-text">
          <h1>Test Runs</h1>
          <p>History of all your API test executions</p>
        </div>
        <button id="new-run-btn" className="btn btn-primary">
          <Play size={16} />
          New Run
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex gap-3 items-center" style={{ marginBottom: 24 }}>
        {['All', 'Completed', 'Failed', 'Running', 'Pending'].map(f => (
          <button key={f}
            className={`btn btn-sm ${f === 'All' ? 'btn-primary' : 'btn-secondary'}`}
            id={`filter-${f.toLowerCase()}`}>
            {f}
          </button>
        ))}
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Status</th>
                <th>Tests</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Duration</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_RUNS.map(run => (
                <tr key={run.id}>
                  <td><span className="font-medium">{run.project}</span></td>
                  <td><StatusBadge status={run.status} /></td>
                  <td>{run.total || '--'}</td>
                  <td>
                    {run.passed > 0
                      ? <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{run.passed}</span>
                      : '--'}
                  </td>
                  <td>
                    {run.failed > 0
                      ? <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>{run.failed}</span>
                      : run.passed > 0 ? <span style={{ color: 'var(--color-success)' }}>0</span> : '--'}
                  </td>
                  <td><code>{run.duration}</code></td>
                  <td className="text-sm text-muted">{run.created}</td>
                  <td>
                    <div className="flex gap-2">
                      <button className="btn btn-ghost btn-sm" id={`view-run-${run.id}`}>View</button>
                      {run.status === 'RUNNING' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div className="progress-bar-track" style={{ width: 80 }}>
                            <div className="progress-bar-fill" style={{ width: `${Math.round(run.passed / 60 * 100)}%` }} />
                          </div>
                          <span className="text-xs text-muted">{Math.round(run.passed / 60 * 100)}%</span>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}
