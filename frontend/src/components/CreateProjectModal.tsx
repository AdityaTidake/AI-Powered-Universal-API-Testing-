/**
 * CreateProjectModal — modal dialog for creating a new project.
 * Uses useCreateProject() mutation; invalidates the projects list on success.
 */
import { useState } from 'react';
import { X, FolderPlus } from 'lucide-react';
import { useCreateProject } from '../store/projectsStore';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function CreateProjectModal({ isOpen, onClose }: Props) {
  const [name, setName]           = useState('');
  const [description, setDesc]    = useState('');
  const createProject             = useCreateProject();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await createProject.mutateAsync({ name: name.trim(), description: description.trim() || undefined });
    setName('');
    setDesc('');
    onClose();
  };

  return (
    <div
      className="modal-backdrop"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 24,
      }}
    >
      <div
        className="card"
        style={{
          width: '100%', maxWidth: 480,
          animation: 'fadeInUp 0.18s ease',
        }}
      >
        {/* Header */}
        <div className="card-header">
          <div className="flex items-center gap-3">
            <div style={{
              width: 38, height: 38,
              background: 'var(--color-primary-muted)',
              borderRadius: 'var(--radius-lg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <FolderPlus size={18} style={{ color: 'var(--color-primary)' }} />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem' }}>New Project</h3>
              <p className="text-sm text-muted" style={{ marginTop: 1 }}>
                Create a project to upload your OpenAPI spec
              </p>
            </div>
          </div>
          <button
            id="close-create-project-modal"
            className="btn btn-ghost btn-icon"
            onClick={onClose}
            type="button"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="form-group">
              <label className="form-label" htmlFor="project-name">
                Project Name <span style={{ color: 'var(--color-danger)' }}>*</span>
              </label>
              <input
                id="project-name"
                className="form-input"
                type="text"
                placeholder="e.g. Payment API"
                value={name}
                onChange={e => setName(e.target.value)}
                maxLength={255}
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="project-description">
                Description <span className="text-muted" style={{ fontWeight: 400 }}>(optional)</span>
              </label>
              <textarea
                id="project-description"
                className="form-input"
                placeholder="Short description of the API..."
                value={description}
                onChange={e => setDesc(e.target.value)}
                rows={3}
                maxLength={2000}
                style={{ resize: 'vertical' }}
              />
            </div>
          </div>

          <div className="card-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <button
              id="cancel-create-project"
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={createProject.isPending}
            >
              Cancel
            </button>
            <button
              id="submit-create-project"
              type="submit"
              className="btn btn-primary"
              disabled={!name.trim() || createProject.isPending}
            >
              {createProject.isPending ? 'Creating…' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
