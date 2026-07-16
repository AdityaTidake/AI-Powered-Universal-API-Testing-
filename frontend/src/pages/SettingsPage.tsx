import AppLayout from '../components/AppLayout';
import { User, Key, Bell, Shield, Copy, Trash2, Plus } from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '../store/authStore';

const MOCK_API_KEYS = [
  { id: '1', name: 'GitHub Actions CI', key: 'sg_live_••••••••••••••••3f9a', created: 'Jul 10, 2026', lastUsed: '2h ago' },
  { id: '2', name: 'Local Dev',          key: 'sg_live_••••••••••••••••8c2d', created: 'Jun 15, 2026', lastUsed: '5d ago' },
];

type Tab = 'profile' | 'api-keys' | 'notifications' | 'security';

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [tab, setTab] = useState<Tab>('profile');

  const TABS: { id: Tab; label: string; icon: typeof User }[] = [
    { id: 'profile',       label: 'Profile',       icon: User   },
    { id: 'api-keys',      label: 'API Keys',      icon: Key    },
    { id: 'notifications', label: 'Notifications', icon: Bell   },
    { id: 'security',      label: 'Security',      icon: Shield },
  ];

  return (
    <AppLayout title="Settings">
      <div className="page-header">
        <div className="page-header-text">
          <h1>Settings</h1>
          <p>Manage your account, API keys, and preferences</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: 28 }}>
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} id={`settings-tab-${id}`}
            className={`tab-btn ${tab === id ? 'active' : ''}`}
            onClick={() => setTab(id)}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Icon size={14} />
              {label}
            </span>
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {tab === 'profile' && (
        <div className="animate-fade-in" style={{ maxWidth: 560 }}>
          <div className="card">
            <div className="card-header"><h3 style={{ fontSize: '1rem' }}>Profile Information</h3></div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Avatar */}
              <div className="flex items-center gap-4">
                <div className="avatar" style={{ width: 56, height: 56, fontSize: '1.25rem' }}>
                  {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) ?? 'U'}
                </div>
                <div>
                  <p className="font-semibold">{user?.full_name || 'User'}</p>
                  <p className="text-sm text-muted">{user?.email}</p>
                  <span className={`badge ${user?.plan === 'pro' ? 'badge-purple' : 'badge-gray'}`}
                    style={{ marginTop: 4, fontSize: '0.7rem' }}>
                    {(user?.plan ?? 'free').toUpperCase()} PLAN
                  </span>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="settings-name">Full Name</label>
                <input id="settings-name" className="form-input" defaultValue={user?.full_name || ''} />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="settings-email">Email Address</label>
                <input id="settings-email" className="form-input" defaultValue={user?.email || ''} type="email" />
              </div>

              {/* Usage */}
              <div style={{ background: 'var(--color-surface-alt)', borderRadius: 'var(--radius-lg)', padding: '16px' }}>
                <div className="flex items-center justify-between" style={{ marginBottom: 10 }}>
                  <span className="text-sm font-medium">Monthly Test Runs</span>
                  <span className="text-sm font-bold">
                    {user?.monthly_run_count ?? 0} / {user?.plan === 'pro' ? '500' : '10'}
                  </span>
                </div>
                <div className="progress-bar-track">
                  <div className="progress-bar-fill"
                    style={{ width: `${Math.min(((user?.monthly_run_count ?? 0) / (user?.plan === 'pro' ? 500 : 10)) * 100, 100)}%` }} />
                </div>
              </div>

              <button id="save-profile-btn" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys Tab */}
      {tab === 'api-keys' && (
        <div className="animate-fade-in">
          <div className="card">
            <div className="card-header">
              <div>
                <h3 style={{ fontSize: '1rem' }}>API Keys</h3>
                <p className="text-sm text-muted" style={{ marginTop: 2 }}>
                  Use these keys for CI/CD pipelines and programmatic access
                </p>
              </div>
              <button id="create-api-key-btn" className="btn btn-primary btn-sm">
                <Plus size={14} />
                New Key
              </button>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Key</th>
                    <th>Created</th>
                    <th>Last Used</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {MOCK_API_KEYS.map(k => (
                    <tr key={k.id}>
                      <td><span className="font-medium">{k.name}</span></td>
                      <td><code style={{ fontSize: '0.8rem' }}>{k.key}</code></td>
                      <td className="text-sm text-muted">{k.created}</td>
                      <td className="text-sm text-muted">{k.lastUsed}</td>
                      <td>
                        <div className="flex gap-2">
                          <button className="btn btn-ghost btn-icon" title="Copy" id={`copy-key-${k.id}`}>
                            <Copy size={14} />
                          </button>
                          <button className="btn btn-danger btn-icon" title="Revoke" id={`revoke-key-${k.id}`}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {tab === 'security' && (
        <div className="animate-fade-in" style={{ maxWidth: 560 }}>
          <div className="card">
            <div className="card-header"><h3 style={{ fontSize: '1rem' }}>Change Password</h3></div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div className="form-group">
                <label className="form-label" htmlFor="current-pw">Current Password</label>
                <input id="current-pw" type="password" className="form-input" placeholder="••••••••" />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="new-pw">New Password</label>
                <input id="new-pw" type="password" className="form-input" placeholder="Min. 8 characters" />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="confirm-pw">Confirm New Password</label>
                <input id="confirm-pw" type="password" className="form-input" placeholder="••••••••" />
              </div>
              <button id="change-password-btn" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
                Update Password
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notifications Tab */}
      {tab === 'notifications' && (
        <div className="animate-fade-in" style={{ maxWidth: 560 }}>
          <div className="card">
            <div className="card-header"><h3 style={{ fontSize: '1rem' }}>Notification Preferences</h3></div>
            <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { id: 'notif-run-complete', label: 'Test run completed',       desc: 'Get notified when a test run finishes' },
                { id: 'notif-run-failed',   label: 'Test run failed',          desc: 'Immediate alerts for failed runs' },
                { id: 'notif-security',     label: 'Security score drop',      desc: 'Alert when OWASP score drops below threshold' },
                { id: 'notif-weekly',       label: 'Weekly digest email',      desc: 'Summary of API health every Monday' },
              ].map(n => (
                <label key={n.id} htmlFor={n.id}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                  <div>
                    <p className="font-medium text-sm">{n.label}</p>
                    <p className="text-xs text-muted" style={{ marginTop: 2 }}>{n.desc}</p>
                  </div>
                  <input id={n.id} type="checkbox" defaultChecked style={{
                    width: 18, height: 18, accentColor: 'var(--color-primary)', cursor: 'pointer',
                  }} />
                </label>
              ))}
              <button id="save-notifications-btn" className="btn btn-primary" style={{ alignSelf: 'flex-start', marginTop: 8 }}>
                Save Preferences
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
