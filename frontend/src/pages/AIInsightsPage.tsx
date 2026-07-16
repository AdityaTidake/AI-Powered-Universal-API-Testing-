import AppLayout from '../components/AppLayout';
import { Brain, Shield, Copy, CheckCircle, AlertTriangle, ChevronDown } from 'lucide-react';
import { useState } from 'react';

const MOCK_ANALYSES = [
  {
    id: '1',
    run: 'Payment API — Run #42',
    rootCause: 'The POST /payments endpoint returns HTTP 500 when the `card_number` field contains spaces. The backend does not sanitize card number input before processing, causing a database constraint violation.',
    suggestedFix: `# Sanitize input before validation
card_number = card_number.replace(' ', '').replace('-', '')
if not re.match(r'^\\d{16}$', card_number):
    raise ValueError("Invalid card number format")`,
    confidence: 94,
    securityScore: 72,
    owaspIssues: [
      { category: 'A03 — Injection', severity: 'high',   desc: 'Unsanitized input passed to payment processor' },
      { category: 'A07 — Auth Failures', severity: 'medium', desc: 'Token not invalidated after password change' },
    ],
    similar: [
      { endpoint: 'POST /orders',  error: 'Input validation failure', fix: 'Added Pydantic validator', score: 0.92 },
      { endpoint: 'PUT /users/me', error: 'SQL injection via name field', fix: 'Parameterized query', score: 0.78 },
    ],
  },
];

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
  const [expanded, setExpanded] = useState<string | null>('1');

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

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {MOCK_ANALYSES.map(analysis => (
          <div key={analysis.id} className="card">
            {/* Collapsible Header */}
            <button
              id={`insight-toggle-${analysis.id}`}
              className="card-header"
              style={{ width: '100%', cursor: 'pointer', background: 'none', border: 'none', textAlign: 'left' }}
              onClick={() => setExpanded(expanded === analysis.id ? null : analysis.id)}
            >
              <div>
                <h3 style={{ fontSize: '1rem' }}>{analysis.run}</h3>
                <p className="text-sm text-muted" style={{ marginTop: 2 }}>
                  Confidence: {analysis.confidence}% · Security Score: {analysis.securityScore}/100
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
                      {analysis.rootCause}
                    </div>
                  </div>

                  {/* Security Score */}
                  <div>
                    <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                      <Shield size={16} style={{ color: 'var(--color-primary)' }} />
                      Security Score
                    </h4>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                      <SecurityGauge score={analysis.securityScore} />
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {analysis.owaspIssues.map(issue => (
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
                            <p className="text-xs text-muted">{issue.desc}</p>
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
                    <button id="copy-fix-btn" className="btn btn-secondary btn-sm" onClick={() => copyFix(analysis.suggestedFix)}>
                      {copied ? <CheckCircle size={13} style={{ color: 'var(--color-success)' }} /> : <Copy size={13} />}
                      {copied ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre style={{ fontSize: '0.82rem', borderRadius: 'var(--radius-lg)' }}>
                    {analysis.suggestedFix}
                  </pre>
                </div>

                {/* RAG — Similar Failures */}
                <div>
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <AlertTriangle size={16} style={{ color: 'var(--color-warning)' }} />
                    Similar Past Failures (RAG Retrieved)
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {analysis.similar.map(s => (
                      <div key={s.endpoint} style={{
                        display: 'flex', alignItems: 'center', gap: 16,
                        background: 'var(--color-surface-alt)',
                        borderRadius: 'var(--radius-lg)',
                        padding: '12px 16px',
                      }}>
                        <div style={{ flex: 1 }}>
                          <code style={{ fontSize: '0.82rem' }}>{s.endpoint}</code>
                          <p className="text-sm text-muted" style={{ marginTop: 2 }}>{s.error}</p>
                          <p className="text-sm" style={{ marginTop: 4, color: 'var(--color-success)' }}>
                            ✓ Fix: {s.fix}
                          </p>
                        </div>
                        <div style={{ textAlign: 'right', flexShrink: 0 }}>
                          <div className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
                            {Math.round(s.score * 100)}% match
                          </div>
                        </div>
                      </div>
                    ))}
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
