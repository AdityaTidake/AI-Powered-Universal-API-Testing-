import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, FolderOpen, Play, BarChart2,
  Brain, Settings, Shield, LogOut, ChevronRight,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';

const NAV_ITEMS = [
  { to: '/dashboard',  label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/projects',   label: 'Projects',    icon: FolderOpen },
  { to: '/runs',       label: 'Test Runs',   icon: Play },
  { to: '/analytics',  label: 'Analytics',   icon: BarChart2 },
  { to: '/ai-insights',label: 'AI Insights', icon: Brain },
  { to: '/orgs',       label: 'Organizations', icon: Shield },
];

const BOTTOM_ITEMS = [
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() ?? 'U';

  return (
    <aside className="sidebar">
      {/* Logo */}
      <NavLink to="/dashboard" className="sidebar-logo">
        <div className="sidebar-logo-icon">SG</div>
        <div className="sidebar-logo-text">
          Spec<span>Guard</span> AI
        </div>
      </NavLink>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <span className="sidebar-section-label">Main</span>
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}

        <span className="sidebar-section-label">Account</span>
        {BOTTOM_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="sidebar-footer">
        {/* Plan badge */}
        <div style={{ marginBottom: '12px' }}>
          <span className={`badge ${user?.plan === 'pro' ? 'badge-purple' : 'badge-gray'}`}>
            <Shield size={10} />
            {user?.plan?.toUpperCase() ?? 'FREE'} Plan
          </span>
          {user?.plan === 'free' && (
            <div style={{ marginTop: '6px', fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
              {user.monthly_run_count ?? 0} / 10 runs this month
            </div>
          )}
        </div>

        {/* User info */}
        <div className="flex items-center gap-3" style={{ marginBottom: '8px' }}>
          <div className="avatar" style={{ width: 32, height: 32, fontSize: '0.75rem' }}>
            {initials}
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div className="truncate text-sm font-medium">{user?.full_name || 'User'}</div>
            <div className="truncate" style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>
              {user?.email}
            </div>
          </div>
          <ChevronRight size={14} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
        </div>

        <button className="btn btn-ghost btn-sm w-full" onClick={handleLogout}
          style={{ justifyContent: 'flex-start', gap: '8px', color: 'var(--color-danger)' }}>
          <LogOut size={15} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
