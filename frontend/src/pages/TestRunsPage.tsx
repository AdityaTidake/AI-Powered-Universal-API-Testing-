/**
 * TestRunsPage — shows all test runs across all user projects (live data).
 * Supports status filtering and real-time polling for active runs.
 */
import { useState } from 'react';
import { Play, Clock, CheckCircle2, XCircle, Loader2, AlertCircle, StopCircle } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import LaunchRunModal from '../components/LaunchRunModal';
import { useProjects } from '../store/projectsStore';
import { useTestRuns, usePollTestRun, useCancelTestRun } from '../store/testRunsStore';
import type { TestRun, TestRunStatus, Project } from '../types';

// ── Status helpers ─────────────────────────────────────────────────────────────
function StatusIcon({ status }: { status: TestRunStatus }) {
  if (status === 'COMPLETED')  return <CheckCircle2 size={14} style={{ color: 'var(--color-success)' }} />;
  if (status === 'FAILED')     return <XCircle      size={14} style={{ color: 'var(--color-danger)'  }} />;
  if (status === 'CANCELLED')  return <StopCircle   size={14} style={{ color: 'var(--color-text-muted)' }} />;
  if (status === 'RUNNING')    return <Loader2      size={14} style={{ color: 'var(--color-info)', animation: 'spin 1s linear infinite' }} />;
  return <Clock size={14} style={{ color: 'var(--color-text-muted)' }} />;
}

function StatusBadge({ status }: { status: TestRunStatus }) {
  const cls: Record<string, string> = {
    COMPLETED: 'badge-success', FAILED: 'badge-danger',
    RUNNING: 'badge-info',      PENDING: 'badge-gray',
    CANCELLED: 'badge-gray',
  };
  return (
    <span className={`badge ${cls[status] ?? 'badge-gray'}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <StatusIcon status={status} />
      {status}
    </span>
  );
}

// ── Per-project rows ───────────────────────────────────────────────────────────
function ProjectRunRows({ project, statusFilter }: { project: Project; statusFilter: string }) {
  const { data: runs, isLoading } = useTestRuns(project.id);

  const filtered = (runs ?? []).filter(r =>
    statusFilter === 'All' || r.status === statusFilter.toUpperCase()
  );

  if (isLoading) {
    return (
      <tr>
        <td colSpan={9} style={{ textAlign: 'center', padding: 12, color: 'var(--color-text-muted)' }}>
          Loading runs for {project.name}…
        </td>
      </tr>
    );
  }

  return (
    <>
      {filtered.map(run => (
        <RunRow key={run.id} run={run} projectName={project.name} projectId={project.id} />
      ))}
    </>
  );
}

// ── Single run row (polls if RUNNING/PENDING) ─────────────────────────────────
function RunRow({ run, projectName, projectId }: { run: TestRun; projectName: string; projectId: string }) {
  const isActive = run.status === 'RUNNING' || run.status === 'PENDING';
  const { data: liveRun } = usePollTestRun(run.id, isActive);
  const r = liveRun ?? run;

  const cancelRun = useCancelTestRun(projectId);

  const passRate = r.total_cases
    ? Math.round(((r.passed_cases ?? 0) / r.total_cases) * 100)
    : null;

  const duration = (() => {
    if (!r.started_at) return '--';
    const end = r.completed_at ? new Date(r.completed_at) : new Date();
    const ms  = end.getTime() - new Date(r.started_at).getTime();
    const s   = Math.floor(ms / 1000);
    return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
  })();

  return (
    <tr>
      <td><span className="font-medium">{projectName}</span></td>
      <td><StatusBadge status={r.status} /></td>
      <td>{r.total_cases ?? '--'}</td>
      <td>
        {r.passed_cases != null
          ? <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{r.passed_cases}</span>
          : '--'}
      </td>
      <td>
        {r.failed_cases != null && r.failed_cases > 0
          ? <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>{r.failed_cases}</span>
          : r.passed_cases != null ? <span style={{ color: 'var(--color-success)' }}>0</span> : '--'}
      </td>
      <td>
        {passRate !== null
          ? (
            <div className="flex items-center gap-2">
              <div className="progress-bar-track" style={{ width: 64 }}>
                <div className="progress-bar-fill" style={{ width: `${passRate}%` }} />
              </div>
              <span className="text-sm">{passRate}%</span>
            </div>
          )
          : '--'}
      </td>
      <td><code>{duration}</code></td>
      <td className="text-sm text-muted">
        {new Date(r.created_at).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })}
      </td>
      <td>
        {isActive && (
          <button
            id={`stop-run-${r.id}`}
            className="btn btn-sm btn-danger"
            disabled={cancelRun.isPending}
            onClick={() => cancelRun.mutate(r.id)}
            title="Stop this run"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}
          >
            <StopCircle size={13} />
            {cancelRun.isPending ? 'Stopping…' : 'Stop'}
          </button>
        )}
      </td>
    </tr>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
const FILTERS = ['All', 'Completed', 'Failed', 'Running', 'Pending', 'Cancelled'];

export default function TestRunsPage() {
  const [filter, setFilter]           = useState('All');
  const [launchOpen, setLaunchOpen]   = useState(false);

  const { data: projects, isLoading: loadingProjects, isError } = useProjects();

  const hasData = !loadingProjects && !isError && projects && projects.length > 0;

  return (
    <AppLayout title="Test Runs">
      <div className="page-header">
        <div className="page-header-text">
          <h1>Test Runs</h1>
          <p>History of all your API test executions</p>
        </div>
        <button id="new-run-btn" className="btn btn-primary" onClick={() => setLaunchOpen(true)}>
          <Play size={16} />
          New Run
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex gap-3 items-center" style={{ marginBottom: 24, flexWrap: 'wrap' }}>
        {FILTERS.map(f => (
          <button
            key={f}
            id={`filter-${f.toLowerCase()}`}
            className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Error */}
      {isError && (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 24, color: 'var(--color-danger)' }}>
          <AlertCircle size={22} />
          <span>Failed to load data. Is the backend running?</span>
        </div>
      )}

      {/* Loading */}
      {loadingProjects && !isError && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200, gap: 12 }}>
          <Loader2 size={24} style={{ color: 'var(--color-primary)', animation: 'spin 1s linear infinite' }} />
          <span className="text-muted">Loading…</span>
        </div>
      )}

      {/* Empty (no projects) */}
      {!loadingProjects && !isError && projects?.length === 0 && (
        <div className="card" style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: 200, textAlign: 'center', gap: 12,
        }}>
          <Play size={32} style={{ color: 'var(--color-text-muted)' }} />
          <p className="text-muted">No projects yet. Create a project first to run tests.</p>
        </div>
      )}

      {/* Runs table */}
      {hasData && (
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
                  <th>Pass Rate</th>
                  <th>Duration</th>
                  <th>Created</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {projects!.map(p => (
                  <ProjectRunRows key={p.id} project={p} statusFilter={filter} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Launch Run modal (pick a project first) */}
      <LaunchRunModal
        isOpen={launchOpen}
        project={projects?.[0] ?? null}
        onClose={() => setLaunchOpen(false)}
      />
    </AppLayout>
  );
}


