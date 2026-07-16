import AppLayout from '../components/AppLayout';
import { FolderOpen, Plus, Trash2, Upload, ExternalLink } from 'lucide-react';

const MOCK_PROJECTS = [
  { id: '1', name: 'Payment API', description: 'Stripe integration endpoints', runs: 42, lastRun: '2h ago',  spec: true  },
  { id: '2', name: 'Auth Service', description: 'JWT login and token management', runs: 18, lastRun: '5h ago',  spec: true  },
  { id: '3', name: 'Product Catalog', description: 'REST endpoints for product management', runs: 7, lastRun: '1d ago',  spec: false },
  { id: '4', name: 'Notification Service', description: 'Push and email notification APIs', runs: 3, lastRun: '3d ago',  spec: true  },
];

export default function ProjectsPage() {
  return (
    <AppLayout title="Projects">
      <div className="page-header">
        <div className="page-header-text">
          <h1>Projects</h1>
          <p>Manage your API projects and OpenAPI specs</p>
        </div>
        <button id="create-project-btn" className="btn btn-primary">
          <Plus size={16} />
          New Project
        </button>
      </div>

      <div className="grid-3">
        {MOCK_PROJECTS.map(p => (
          <div key={p.id} className="card card-hover" style={{ cursor: 'pointer' }}>
            <div className="card-body">
              <div className="flex items-start justify-between" style={{ marginBottom: 12 }}>
                <div style={{
                  width: 44, height: 44,
                  background: 'var(--color-primary-muted)',
                  borderRadius: 'var(--radius-lg)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <FolderOpen size={22} style={{ color: 'var(--color-primary)' }} />
                </div>
                <div className="flex gap-2">
                  {p.spec && (
                    <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                      Spec ✓
                    </span>
                  )}
                </div>
              </div>

              <h3 style={{ fontSize: '1rem', marginBottom: 4 }}>{p.name}</h3>
              <p className="text-sm text-muted" style={{ marginBottom: 16, lineHeight: 1.5 }}>
                {p.description}
              </p>

              <div className="flex items-center justify-between text-sm" style={{ marginBottom: 16 }}>
                <span className="text-muted">{p.runs} runs</span>
                <span className="text-muted">Last run: {p.lastRun}</span>
              </div>

              <div className="flex gap-2">
                <button className="btn btn-primary btn-sm flex-1" id={`run-tests-${p.id}`}>
                  Run Tests
                </button>
                <button className="btn btn-secondary btn-icon" title="Upload Spec" id={`upload-spec-${p.id}`}>
                  <Upload size={15} />
                </button>
                <button className="btn btn-secondary btn-icon" title="View" id={`view-project-${p.id}`}>
                  <ExternalLink size={15} />
                </button>
                <button className="btn btn-danger btn-icon" title="Delete" id={`delete-project-${p.id}`}>
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          </div>
        ))}

        {/* New Project Card */}
        <div className="card" style={{
          cursor: 'pointer', border: '2px dashed var(--color-border)',
          background: 'var(--color-surface-alt)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          minHeight: 220,
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              width: 48, height: 48, margin: '0 auto 12px',
              background: 'var(--color-primary-muted)',
              borderRadius: 'var(--radius-lg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Plus size={24} style={{ color: 'var(--color-primary)' }} />
            </div>
            <p className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              New Project
            </p>
            <p className="text-sm text-muted" style={{ marginTop: 4 }}>
              Upload an OpenAPI spec to get started
            </p>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
