'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UploadResultProvider } from './upload-result-context';

const NAV_ITEMS = [
  { href: '/dashboard',           label: 'Overview',  icon: '◈' },
  { href: '/dashboard/documents', label: 'Resume',    icon: '📄' },
  { href: '/dashboard/skills',    label: 'Skills',    icon: '🛠' },
  { href: '/dashboard/roles',     label: 'Roles',     icon: '🗺' },
  { href: '/dashboard/jobs',      label: 'Jobs',      icon: '💼' },
  { href: '/dashboard/chat',      label: 'Mentor',    icon: '✦' },
  { href: '/dashboard/settings',  label: 'Settings',  icon: '⚙' },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => { setMobileOpen(false); }, [pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  const activeLabel = NAV_ITEMS.find(n => n.href === pathname)?.label ?? 'Dashboard';

  return (
    <UploadResultProvider>
      <div style={{ display: 'flex', minHeight: '100vh' }}>

        {/* ── Desktop sidebar ─────────────────────────────── */}
        <aside
          className="hidden lg:flex"
          style={{
            width: '220px',
            flexShrink: 0,
            background: 'var(--bg-surface)',
            borderRight: '1px solid var(--border-subtle)',
            flexDirection: 'column',
            padding: '1.25rem 0',
            position: 'sticky',
            top: 0,
            height: '100vh',
            overflowY: 'auto',
          }}
        >
          {/* Logo */}
          <div style={{ padding: '0 1.25rem 1.5rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '0.5rem' }}>
            <Link href="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', textDecoration: 'none' }}>
              <div style={{
                width: '32px', height: '32px', borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--brand-500), var(--accent-400))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'white', fontWeight: 700, fontSize: '0.875rem',
                fontFamily: 'var(--font-display)',
              }}>S</div>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
                Skill Sync
              </span>
            </Link>
          </div>

          {/* Nav links */}
          <nav style={{ flex: 1, padding: '0 0.75rem' }}>
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.625rem',
                    padding: '0.6rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    margin: '0.125rem 0',
                    fontSize: '0.875rem',
                    fontWeight: active ? 600 : 400,
                    color: active ? 'var(--brand-600)' : 'var(--text-secondary)',
                    background: active ? 'var(--brand-50)' : 'transparent',
                    textDecoration: 'none',
                    transition: 'all var(--transition-fast)',
                    borderLeft: active ? '2.5px solid var(--brand-500)' : '2.5px solid transparent',
                  }}
                >
                  <span style={{ fontSize: '0.9rem', lineHeight: 1 }}>{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* ── Mobile overlay ───────────────────────────────── */}
        {mobileOpen && (
          <div
            className="lg:hidden fixed inset-0 z-40"
            style={{ background: 'rgba(30,34,53,0.5)', backdropFilter: 'blur(4px)' }}
            onClick={() => setMobileOpen(false)}
          />
        )}

        {/* ── Mobile drawer ────────────────────────────────── */}
        <div
          className="lg:hidden fixed inset-y-0 left-0 z-50"
          style={{
            width: '260px',
            background: 'var(--bg-surface)',
            borderRight: '1px solid var(--border-subtle)',
            transform: mobileOpen ? 'translateX(0)' : 'translateX(-100%)',
            transition: 'transform 300ms ease',
            display: 'flex',
            flexDirection: 'column',
            padding: '1.25rem 0',
            boxShadow: mobileOpen ? 'var(--shadow-lg)' : 'none',
          }}      
        >
          {/* Drawer header */}
          <div style={{
            padding: '0 1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
            marginBottom: '0.5rem',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            
          }}>
            <Link href="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', textDecoration: 'none' }}>
              <div style={{
                width: '32px', height: '32px', borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--brand-500), var(--accent-400))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'white', fontWeight: 700, fontSize: '0.875rem',
              }}>S</div>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
                Skill Sync
              </span>
            </Link>
            <button
              onClick={() => setMobileOpen(false)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.25rem', color: 'var(--text-muted)', lineHeight: 1, padding: '4px' }}
              aria-label="Close menu"
            >
              ×
            </button>
          </div>

          {/* Drawer nav */}
          <nav style={{ flex: 1, padding: '0 0.75rem', overflowY: 'auto' }}>
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.625rem',
                    padding: '0.7rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    margin: '0.125rem 0',
                    fontSize: '0.9375rem',
                    fontWeight: active ? 600 : 400,
                    color: active ? 'var(--brand-600)' : 'var(--text-secondary)',
                    background: active ? 'var(--brand-50)' : 'transparent',
                    textDecoration: 'none',
                    borderLeft: active ? '2.5px solid var(--brand-500)' : '2.5px solid transparent',
                  }}
                >
                  <span style={{ fontSize: '1rem', lineHeight: 1 }}>{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* ── Main content ─────────────────────────────────── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>

          {/* Mobile topbar */}
          <header
            className="lg:hidden sticky top-0 z-30 flex items-center gap-3 px-4 py-3"
            style={{
              background: 'rgba(244,245,247,0.92)',
              backdropFilter: 'blur(8px)',
              borderBottom: '1px solid var(--border-subtle)',
            }}
          >
            <button
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="6"  x2="21" y2="6"  />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
              {activeLabel}
            </span>
            <div style={{
              marginLeft: 'auto', width: '28px', height: '28px', borderRadius: '7px',
              background: 'linear-gradient(135deg, var(--brand-500), var(--accent-400))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontSize: '0.75rem', fontWeight: 700,
            }}>S</div>
          </header>

          {/* Page content */}
          <main style={{ flex: 1, padding: '2rem 1rem' }} className="sm:p-8">
            <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
              {children}
            </div>
          </main>
        </div>

      </div>
    </UploadResultProvider>
  );
}
