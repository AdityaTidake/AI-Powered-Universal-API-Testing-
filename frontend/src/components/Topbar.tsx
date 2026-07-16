import { Bell, Search } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

interface TopbarProps {
  title: string;
  subtitle?: string;
}

export default function Topbar({ title, subtitle }: TopbarProps) {
  const { user } = useAuthStore();

  return (
    <header className="topbar">
      <div className="topbar-breadcrumb">
        <strong>{title}</strong>
        {subtitle && (
          <>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
              style={{ width: 14, height: 14, color: 'var(--color-text-muted)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
            <span>{subtitle}</span>
          </>
        )}
      </div>

      <div className="topbar-actions">
        {/* Search trigger */}
        <button className="btn btn-ghost btn-icon" title="Search" aria-label="Search">
          <Search size={18} style={{ color: 'var(--color-text-secondary)' }} />
        </button>

        {/* Notifications */}
        <button className="btn btn-ghost btn-icon" title="Notifications" aria-label="Notifications"
          style={{ position: 'relative' }}>
          <Bell size={18} style={{ color: 'var(--color-text-secondary)' }} />
          <span style={{
            position: 'absolute', top: 6, right: 6,
            width: 7, height: 7,
            background: 'var(--color-primary)',
            borderRadius: '50%',
            border: '1.5px solid white',
          }} />
        </button>

        {/* User avatar */}
        <div className="avatar" style={{ fontSize: '0.8rem' }}>
          {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) ?? 'U'}
        </div>
      </div>
    </header>
  );
}
