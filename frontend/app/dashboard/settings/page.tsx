'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import type { User } from '@/lib/auth';

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [logoutLoading, setLogoutLoading] = useState(false);

  useEffect(() => {
    api.get<User>('/auth/me/')
      .then((r) => setUser(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    setLogoutLoading(true);
    try {
      await api.post('/auth/logout/');
    } catch {}
    finally {
      router.push('/login');
    }
  }

  if (loading) return (
    <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
      <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Loading settings…
    </div>
  );

  const initials = user?.email ? user.email.slice(0, 2).toUpperCase() : '??';

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 style={{ fontFamily: 'var(--font-display)', marginBottom: '0.35rem' }}>Settings</h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Manage your account and preferences.</p>
      </div>

      {/* Account card */}
      <div className="card anim-fade-up" style={{ padding: '1.5rem' }}>
        <p className="section-label">Account Details</p>

        <div className="flex items-center gap-4 mb-5">
          <div className="w-14 h-14 rounded-xl flex items-center justify-center text-white text-lg font-bold flex-shrink-0"
            style={{
              background: 'linear-gradient(135deg, var(--brand-500), var(--accent-400))',
              boxShadow: '0 4px 14px rgba(77,94,199,0.3)',
              fontFamily: 'var(--font-display)',
            }}>
            {initials}
          </div>
          <div>
            <p className="font-semibold text-base" style={{ color: 'var(--text-primary)', margin: 0 }}>{user?.email}</p>
            <span className="badge badge-brand mt-1 capitalize" style={{ fontSize: '0.7rem' }}>
              {(user as any)?.role || 'Member'}
            </span>
          </div>
        </div>

        <div className="space-y-0.5">
          {[
            { label: 'Email',      value: user?.email },
            { label: 'Role',       value: <span className="capitalize badge badge-brand">{(user as any)?.role || 'member'}</span> },
            { label: 'Account ID', value: <code className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{(user as any)?.id || '—'}</code> },
          ].map((row, i) => (
            <div key={i} className="flex justify-between items-center py-3"
              style={{ borderTop: '1px solid var(--border-subtle)' }}>
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{row.label}</span>
              <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{row.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Session card */}
      <div className="card anim-fade-up delay-1" style={{ padding: '1.5rem', borderColor: '#fca5a5' }}>
        <p className="section-label" style={{ color: 'var(--error)' }}>Session</p>

        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="font-medium text-sm" style={{ color: 'var(--text-primary)', margin: '0 0 0.2rem' }}>Sign Out</p>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>You'll be redirected to the login page.</p>
          </div>
          <button
            onClick={handleLogout}
            disabled={logoutLoading}
            className="btn btn-danger flex-shrink-0">
            {logoutLoading ? 'Signing out…' : 'Logout'}
          </button>
        </div>
      </div>
    </div>
  );
}












