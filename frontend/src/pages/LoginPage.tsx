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

export default function LoginPage() {
  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [showPw,   setShowPw]   = useState(false);
  const [errors,   setErrors]   = useState<{ email?: string; password?: string }>({});

  const validate = () => {
    const e: typeof errors = {};
    if (!email)                         e.email    = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(email)) e.email = 'Enter a valid email';
    if (!password)                      e.password = 'Password is required';
    else if (password.length < 6)       e.password = 'At least 6 characters';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    try {
      await login(email, password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })
        ?.response?.data?.message ?? 'Invalid credentials';
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
            The AI-powered API testing platform that finds bugs before production does.
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
            <h2>Sign in to SpecGuard AI</h2>
            <p className="text-secondary" style={{ marginTop: 4 }}>
              Enter your credentials to access your workspace
            </p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            {/* Email */}
            <div className="form-group">
              <label className="form-label" htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                className={`form-input${errors.email ? ' error' : ''}`}
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                autoFocus
              />
              {errors.email && <span className="form-error">{errors.email}</span>}
            </div>

            {/* Password */}
            <div className="form-group">
              <label className="form-label" htmlFor="password">Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  className={`form-input${errors.password ? ' error' : ''}`}
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                  style={{ paddingRight: 44 }}
                />
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

            <button id="login-submit-btn" type="submit" className="btn btn-primary w-full"
              disabled={isLoading} style={{ marginTop: 4 }}>
              {isLoading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : null}
              {isLoading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="auth-footer-text">
            Don't have an account?{' '}
            <Link to="/register" className="auth-link">Create one free</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
