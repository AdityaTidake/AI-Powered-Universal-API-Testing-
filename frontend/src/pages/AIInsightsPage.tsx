import AppLayout from '../components/AppLayout';
import { Brain, Shield, Copy, CheckCircle, AlertTriangle, ChevronDown } from 'lucide-react';
import { useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '../api';
import { Loader2 } from 'lucide-react';

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'badge-danger',
  high:     'badge-danger',
  medium:   'badge-warning',
  low:      'badge-info',
};

function SecurityGauge({ score }: { score: number }) {
  const radius  = 52;
  const circ    = 2 * Math.PI * radius;
  const offset  = circ - (score / 100) * circ;
  const color   = score >= 80 ? 'var(--color-success)' : score >= 60 ? 'var(--color-warning)' : 'var(--color-danger)';
  return (
    <div style={{ textAlign: 'center' }}>
      <svg width={130} height={130} viewBox="0 0 130 130">
        <circle cx="65" cy="65" r={radius} fill="none" stroke="var(--color-border)" strokeWidth={10} />
        <circle cx="65" cy="65" r={radius} fill="none" stroke={color} strokeWidth={10}
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 65 65)" />
        <text x="65" y="60" textAnchor="middle" fontSize="22" fontWeight="800"
          fill="var(--color-text-primary)">{score}</text>
        <text x="65" y="78" textAnchor="middle" fontSize="10"
          fill="var(--color-text-muted)">/ 100</text>
      </svg>
      <p className="text-sm font-semibold" style={{ color, marginTop: -8 }}>
        {score >= 80 ? 'Good' : score >= 60 ? 'Needs Attention' : 'Critical'}
      </p>
    </div>
  );
}

export default function AIInsightsPage() {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data: analyses, isLoading } = useQuery({
    queryKey: ['ai-insights'],
    queryFn: async () => {
      const res = await analyticsAPI.insights();
      return res.data;
    },
  });

  const copyFix = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AppLayout title="AI Insights">
      <div className="page-header">
        <div className="page-header-text">
          <h1>AI Insights</h1>
          <p>Root cause analysis, suggested fixes, and security scoring powered by Gemini AI</p>
        </div>
        <div className="flex gap-2 items-center">
          <span className="badge badge-purple">
            <Brain size={11} />
            Gemini Pro
          </span>
        </div>
      </div>

      {isLoading && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200, gap: 12 }}>
          <Loader2 size={24} style={{ color: 'var(--color-primary)', animation: 'spin 1s linear infinite' }} />
          <span className="text-muted">Loading insights…</span>
        </div>
      )}

      {!isLoading && analyses?.length === 0 && (
        <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>
          <Brain size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
          <h3>No AI Insights yet</h3>
          <p style={{ marginTop: 8 }}>Run a test that fails with AI enabled to see root cause analysis here.</p>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {analyses?.map(analysis => (
          <div key={analysis.id} className="card">
            {/* Collapsible Header */}
            <button
              id={`insight-toggle-${analysis.id}`}
              className="card-header"
              style={{ width: '100%', cursor: 'pointer', background: 'none', border: 'none', textAlign: 'left' }}
              onClick={() => setExpanded(expanded === analysis.id ? null : analysis.id)}
            >
              <div>
                <h3 style={{ fontSize: '1rem' }}>Endpoint: {analysis.endpoint}</h3>
                <p className="text-sm text-muted" style={{ marginTop: 2 }}>
                  Confidence: {analysis.confidence}% · Security Score: {analysis.security_score}/100
                </p>
              </div>
              <ChevronDown size={20} style={{
                color: 'var(--color-text-muted)',
                transform: expanded === analysis.id ? 'rotate(180deg)' : undefined,
                transition: 'transform 0.2s',
              }} />
            </button>

            {expanded === analysis.id && (
              <div className="card-body animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
                {/* Main grid */}
                <div className="grid-2" style={{ gap: 24 }}>
                  {/* Root Cause */}
                  <div>
                    <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                      <Brain size={16} style={{ color: 'var(--color-primary)' }} />
                      Root Cause Analysis
                    </h4>
                    <div style={{
                      background: 'var(--color-primary-bg)',
                      border: '1px solid var(--color-primary-muted)',
                      borderRadius: 'var(--radius-lg)',
                      padding: '14px 16px',
                      fontSize: '0.875rem',
                      lineHeight: 1.7,
                      color: 'var(--color-text-primary)',
                    }}>
                      {analysis.root_cause}
                    </div>
                  </div>

                  {/* Security Score */}
                  <div>
                    <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                      <Shield size={16} style={{ color: 'var(--color-primary)' }} />
                      Security Score
                    </h4>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                      <SecurityGauge score={analysis.security_score} />
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {analysis.owasp_issues?.map(issue => (
                          <div key={issue.category} style={{
                            background: 'var(--color-surface-alt)',
                            borderRadius: 'var(--radius-md)',
                            padding: '10px 14px',
                          }}>
                            <div className="flex items-center justify-between" style={{ marginBottom: 4 }}>
                              <span className="text-sm font-semibold">{issue.category}</span>
                              <span className={`badge ${SEVERITY_COLORS[issue.severity]}`}
                                style={{ fontSize: '0.65rem', textTransform: 'uppercase' }}>
                                {issue.severity}
                              </span>
                            </div>
                            <p className="text-xs text-muted">{issue.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Suggested Fix */}
                <div>
                  <div className="flex items-center justify-between" style={{ marginBottom: 12 }}>
                    <h4 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <CheckCircle size={16} style={{ color: 'var(--color-success)' }} />
                      Suggested Fix
                    </h4>
                    <button id="copy-fix-btn" className="btn btn-secondary btn-sm" onClick={() => copyFix(analysis.suggested_fix)}>
                      {copied ? <CheckCircle size={13} style={{ color: 'var(--color-success)' }} /> : <Copy size={13} />}
                      {copied ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre style={{ fontSize: '0.82rem', borderRadius: 'var(--radius-lg)' }}>
                    {analysis.suggested_fix}
                  </pre>
                </div>

                {/* RAG — Similar Failures (Mocked for now since schema doesn't have it yet) */}
                <div>
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <AlertTriangle size={16} style={{ color: 'var(--color-warning)' }} />
                    Similar Past Failures (RAG Retrieved)
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 16,
                      background: 'var(--color-surface-alt)',
                      borderRadius: 'var(--radius-lg)',
                      padding: '12px 16px',
                    }}>
                      <div style={{ flex: 1 }}>
                        <code style={{ fontSize: '0.82rem' }}>POST /users</code>
                        <p className="text-sm text-muted" style={{ marginTop: 2 }}>Input validation failure</p>
                        <p className="text-sm" style={{ marginTop: 4, color: 'var(--color-success)' }}>
                          ✓ Fix: Added Pydantic validator
                        </p>
                      </div>
                      <div style={{ textAlign: 'right', flexShrink: 0 }}>
                        <div className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
                          87% match
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </AppLayout>
  );
}
