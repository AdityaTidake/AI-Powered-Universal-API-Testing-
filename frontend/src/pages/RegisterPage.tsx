import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, Zap, Lock, BarChart2 } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import toast from 'react-hot-toast';

const FEATURES = [
  { icon: Zap,       text: 'Auto-generate tests from OpenAPI specs' },
  { icon: Shield,    text: 'OWASP security scoring built-in' },
  { icon: BarChart2, text: 'Real-time analytics & AI root-cause analysis' },
  { icon: Lock,      text: 'JWT auth with multi-tenant workspace support' },
];

export default function RegisterPage() {
  const { register, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const [form, setForm] = useState({ full_name: '', email: '', password: '', org_name: '' });
  const [showPw, setShowPw] = useState(false);
  const [errors, setErrors] = useState<Partial<typeof form>>({});

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const validate = () => {
    const e: typeof errors = {};
    if (!form.full_name)               e.full_name = 'Full name is required';
    if (!form.email)                   e.email     = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'Enter a valid email';
    if (!form.password)                e.password  = 'Password is required';
    else if (form.password.length < 8) e.password  = 'At least 8 characters';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!validate()) return;
    try {
      await register(form.email, form.password, form.full_name, form.org_name || undefined);
      toast.success('Account created! Welcome to SpecGuard AI 🎉');
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })
        ?.response?.data?.message ?? 'Registration failed';
      toast.error(msg);
    }
  };

  return (
    <div className="auth-page">
      {/* Brand Side */}
      <div className="auth-brand">
        <div className="auth-brand-content">
          <div className="auth-brand-logo">⚡ SpecGuard<span> AI</span></div>
          <p className="auth-brand-tagline">
            Join hundreds of developers who ship APIs with confidence.
          </p>
        </div>
        <div className="auth-brand-features">
          {FEATURES.map(({ icon: Icon, text }) => (
            <div key={text} className="auth-feature-item">
              <Icon size={16} style={{ flexShrink: 0 }} />
              <span>{text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Form Side */}
      <div className="auth-form-side">
        <div className="auth-form-container">
          <div className="auth-form-header">
            <h2>Create your account</h2>
            <p className="text-secondary" style={{ marginTop: 4 }}>
              Free plan · No credit card required
            </p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="form-group">
              <label className="form-label" htmlFor="full_name">Full name</label>
              <input id="full_name" type="text" className={`form-input${errors.full_name ? ' error' : ''}`}
                placeholder="Jane Doe" value={form.full_name} onChange={set('full_name')} autoFocus />
              {errors.full_name && <span className="form-error">{errors.full_name}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="reg-email">Email address</label>
              <input id="reg-email" type="email" className={`form-input${errors.email ? ' error' : ''}`}
                placeholder="you@example.com" value={form.email} onChange={set('email')} autoComplete="email" />
              {errors.email && <span className="form-error">{errors.email}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="reg-password">Password</label>
              <div style={{ position: 'relative' }}>
                <input id="reg-password" type={showPw ? 'text' : 'password'}
                  className={`form-input${errors.password ? ' error' : ''}`}
                  placeholder="Min. 8 characters" value={form.password} onChange={set('password')}
                  style={{ paddingRight: 44 }} />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  aria-label={showPw ? 'Hide password' : 'Show password'}
                  style={{
                    position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--color-text-muted)', display: 'flex',
                  }}>
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <span className="form-error">{errors.password}</span>}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="org_name">
                Organization name <span style={{ color: 'var(--color-text-muted)' }}>(optional)</span>
              </label>
              <input id="org_name" type="text" className="form-input"
                placeholder="My Company" value={form.org_name} onChange={set('org_name')} />
              <span className="form-hint">Creates a team workspace for collaboration</span>
            </div>

            <button id="register-submit-btn" type="submit" className="btn btn-primary w-full"
              disabled={isLoading} style={{ marginTop: 4 }}>
              {isLoading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : null}
              {isLoading ? 'Creating account…' : 'Create free account'}
            </button>
          </form>

          <p className="auth-footer-text">
            Already have an account?{' '}
            <Link to="/login" className="auth-link">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
