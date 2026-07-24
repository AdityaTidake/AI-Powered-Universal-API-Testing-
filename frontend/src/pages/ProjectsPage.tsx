/**
 * ProjectsPage — lists user's projects from the live API.
 * Supports: create project, upload OpenAPI spec, launch test run, delete project.
 */
import { useRef, useState } from 'react';
import { FolderOpen, Plus, Trash2, Upload, Play, Loader2, AlertCircle } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import CreateProjectModal from '../components/CreateProjectModal';
import LaunchRunModal from '../components/LaunchRunModal';
import { useProjects, useDeleteProject, useUploadSpec } from '../store/projectsStore';
import type { Project } from '../types';

export default function ProjectsPage() {
  const { data: projects, isLoading, isError } = useProjects();
  const deleteProject = useDeleteProject();
  const uploadSpec    = useUploadSpec();

  const [createOpen, setCreateOpen]           = useState(false);
  const [launchProject, setLaunchProject]     = useState<Project | null>(null);
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const handleFileChange = (projectId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadSpec.mutate({ id: projectId, file });
      e.target.value = '';
    }
  };

  const handleDelete = (project: Project) => {
    if (!window.confirm(`Delete project "${project.name}"? This cannot be undone.`)) return;
    deleteProject.mutate(project.id);
  };

  return (
    <AppLayout title="Projects">
      <div className="page-header">
        <div className="page-header-text">
          <h1>Projects</h1>
          <p>Manage your API projects and OpenAPI specs</p>
        </div>
        <button id="create-project-btn" className="btn btn-primary" onClick={() => setCreateOpen(true)}>
          <Plus size={16} />
          New Project
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200, gap: 12 }}>
          <Loader2 size={24} style={{ color: 'var(--color-primary)', animation: 'spin 1s linear infinite' }} />
          <span className="text-muted">Loading projects…</span>
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="card" style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: 24, color: 'var(--color-danger)',
        }}>
          <AlertCircle size={22} />
          <span>Failed to load projects. Is the backend running?</span>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && projects?.length === 0 && (
        <div className="card" style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: 260, textAlign: 'center', gap: 16,
        }}>
          <div style={{
            width: 56, height: 56,
            background: 'var(--color-primary-muted)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <FolderOpen size={28} style={{ color: 'var(--color-primary)' }} />
          </div>
          <div>
            <p className="font-semibold" style={{ fontSize: '1rem' }}>No projects yet</p>
            <p className="text-sm text-muted" style={{ marginTop: 4 }}>
              Create your first project and upload an OpenAPI spec to get started.
            </p>
          </div>
          <button id="create-first-project-btn" className="btn btn-primary" onClick={() => setCreateOpen(true)}>
            <Plus size={16} /> New Project
          </button>
        </div>
      )}

      {/* Projects grid */}
      {!isLoading && !isError && projects && projects.length > 0 && (
        <div className="grid-3">
          {projects.map(p => (
            <div key={p.id} className="card card-hover" style={{ cursor: 'default' }}>
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
                    {p.openapi_spec && (
                      <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                        Spec ✓
                      </span>
                    )}
                  </div>
                </div>

                <h3 style={{ fontSize: '1rem', marginBottom: 4 }}>{p.name}</h3>
                <p className="text-sm text-muted" style={{ marginBottom: 16, lineHeight: 1.5 }}>
                  {p.description || <span style={{ fontStyle: 'italic' }}>No description</span>}
                </p>

                <div className="flex items-center justify-between text-sm" style={{ marginBottom: 16 }}>
                  <span className="text-muted">
                    Created {new Date(p.created_at).toLocaleDateString()}
                  </span>
                  {!p.openapi_spec && (
                    <span style={{ color: 'var(--color-warning)', fontSize: '0.75rem' }}>
                      ⚠ No spec
                    </span>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    id={`run-tests-${p.id}`}
                    className="btn btn-primary btn-sm flex-1"
                    onClick={() => setLaunchProject(p)}
                    disabled={!p.openapi_spec}
                    title={!p.openapi_spec ? 'Upload a spec first' : 'Run Tests'}
                  >
                    <Play size={14} />
                    Run Tests
                  </button>

                  {/* Hidden file input for spec upload */}
                  <input
                    type="file"
                    accept=".yaml,.yml,.json"
                    ref={el => { fileInputRefs.current[p.id] = el; }}
                    onChange={e => handleFileChange(p.id, e)}
                    style={{ display: 'none' }}
                    id={`spec-file-${p.id}`}
                  />
                  <button
                    id={`upload-spec-${p.id}`}
                    className="btn btn-secondary btn-icon"
                    title="Upload OpenAPI Spec"
                    onClick={() => fileInputRefs.current[p.id]?.click()}
                    disabled={uploadSpec.isPending}
                  >
                    <Upload size={15} />
                  </button>

                  <button
                    id={`delete-project-${p.id}`}
                    className="btn btn-danger btn-icon"
                    title="Delete Project"
                    onClick={() => handleDelete(p)}
                    disabled={deleteProject.isPending}
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Add new card */}
          <div
            className="card"
            style={{
              cursor: 'pointer', border: '2px dashed var(--color-border)',
              background: 'var(--color-surface-alt)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              minHeight: 220,
              transition: 'border-color 0.2s, background 0.2s',
            }}
            onClick={() => setCreateOpen(true)}
            id="add-project-card"
          >
            <div style={{ textAlign: 'center' }}>
              <div style={{
                width: 48, height: 48, margin: '0 auto 12px',
                background: 'var(--color-primary-muted)',
                borderRadius: 'var(--radius-lg)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Plus size={24} style={{ color: 'var(--color-primary)' }} />
              </div>
              <p className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>New Project</p>
              <p className="text-sm text-muted" style={{ marginTop: 4 }}>
                Upload an OpenAPI spec to get started
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <CreateProjectModal isOpen={createOpen} onClose={() => setCreateOpen(false)} />
      <LaunchRunModal
        isOpen={!!launchProject}
        project={launchProject}
        onClose={() => setLaunchProject(null)}
      />
    </AppLayout>
  );
}
