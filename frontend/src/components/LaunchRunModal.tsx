/**
 * LaunchRunModal — modal to configure and launch a test run for a project.
 * Accepts base URL, test types, and AI enable toggle.
 */
import { useState } from 'react';
import { X, Play, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useCreateTestRun } from '../store/testRunsStore';
import type { Project } from '../types';

type TestType = 'functional' | 'edge' | 'security' | 'ai';

const TEST_TYPE_OPTIONS: { value: TestType; label: string; desc: string }[] = [
  { value: 'functional', label: 'Functional',  desc: 'Happy-path and standard contract tests' },
  { value: 'edge',       label: 'Edge Cases',  desc: 'Boundary, null, and invalid input tests' },
  { value: 'security',   label: 'Security',    desc: 'OWASP injection and auth bypass tests' },
  { value: 'ai',         label: 'AI-Generated',desc: 'Gemini/Ollama generated test scenarios' },
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
  project: Project | null;
}

export default function LaunchRunModal({ isOpen, onClose, project }: Props) {
  const navigate = useNavigate();

  const [baseUrl, setBaseUrl]     = useState('');
  const [types, setTypes]         = useState<TestType[]>(['functional']);
  const [enableAi, setEnableAi]   = useState(false);

  const createRun = useCreateTestRun(project?.id ?? '');

  if (!isOpen || !project) return null;

  const toggleType = (t: TestType) => {
    setTypes(prev =>
      prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!baseUrl.trim() || types.length === 0) return;
    await createRun.mutateAsync({
      base_url: baseUrl.trim(),
      types,
      enable_ai: enableAi,
    });
    onClose();
    navigate('/runs');
  };

  return (
    <div
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
        style={{ width: '100%', maxWidth: 520, animation: 'fadeInUp 0.18s ease' }}
      >
        {/* Header */}
        <div className="card-header">
          <div className="flex items-center gap-3">
            <div style={{
              width: 38, height: 38,
              background: 'var(--color-success-bg)',
              borderRadius: 'var(--radius-lg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Play size={18} style={{ color: 'var(--color-success)' }} />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem' }}>Launch Test Run</h3>
              <p className="text-sm text-muted" style={{ marginTop: 1 }}>
                {project.name}
              </p>
            </div>
          </div>
          <button id="close-launch-run-modal" className="btn btn-ghost btn-icon" onClick={onClose} type="button">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Base URL */}
            <div className="form-group">
              <label className="form-label" htmlFor="run-base-url">
                Target Base URL <span style={{ color: 'var(--color-danger)' }}>*</span>
              </label>
              <input
                id="run-base-url"
                className="form-input"
                type="url"
                placeholder="https://api.example.com"
                value={baseUrl}
                onChange={e => setBaseUrl(e.target.value)}
                required
                autoFocus
              />
              <p className="text-xs text-muted" style={{ marginTop: 6 }}>
                The API server to run tests against.
              </p>
            </div>

            {/* Test Types */}
            <div className="form-group">
              <label className="form-label">Test Types</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
                {TEST_TYPE_OPTIONS.map(opt => (
                  <label
                    key={opt.value}
                    id={`type-${opt.value}`}
                    style={{
                      display: 'flex', alignItems: 'flex-start', gap: 12,
                      padding: '10px 14px',
                      border: `1.5px solid ${types.includes(opt.value) ? 'var(--color-primary)' : 'var(--color-border)'}`,
                      borderRadius: 'var(--radius-md)',
                      background: types.includes(opt.value) ? 'var(--color-primary-muted)' : 'var(--color-surface-alt)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={types.includes(opt.value)}
                      onChange={() => toggleType(opt.value)}
                      style={{ marginTop: 2, accentColor: 'var(--color-primary)' }}
                    />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{opt.label}</div>
                      <div className="text-xs text-muted" style={{ marginTop: 2 }}>{opt.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* AI Toggle */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '12px 14px',
              border: `1.5px solid ${enableAi ? 'var(--color-primary)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-md)',
              background: enableAi ? 'var(--color-primary-muted)' : 'var(--color-surface-alt)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
              onClick={() => setEnableAi(v => !v)}
            >
              <div className="flex items-center gap-2">
                <Zap size={16} style={{ color: enableAi ? 'var(--color-primary)' : 'var(--color-text-muted)' }} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>Enable AI Analysis</div>
                  <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                    Use Gemini/Ollama to analyze failures and score risk
                  </div>
                </div>
              </div>
              <div style={{
                width: 40, height: 22, borderRadius: 11,
                background: enableAi ? 'var(--color-primary)' : 'var(--color-border)',
                position: 'relative', transition: 'background 0.2s',
                flexShrink: 0,
              }}>
                <div style={{
                  position: 'absolute', top: 3, left: enableAi ? 20 : 3,
                  width: 16, height: 16, borderRadius: '50%',
                  background: '#fff',
                  transition: 'left 0.2s',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                }} />
              </div>
            </div>
          </div>

          <div className="card-footer" style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <button
              id="cancel-launch-run"
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={createRun.isPending}
            >
              Cancel
            </button>
            <button
              id="submit-launch-run"
              type="submit"
              className="btn btn-primary"
              disabled={!baseUrl.trim() || types.length === 0 || createRun.isPending}
            >
              <Play size={15} />
              {createRun.isPending ? 'Launching…' : 'Launch Run'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
