'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useUploadResult } from '../upload-result-context';

interface Role {
  id: string;
  title: string;
  description: string; 
  match_score?: number;
}

// Shape of roles returned by the documents upload endpoint
interface ResumeRole {
  role: string;
  description: string;
  skills: string;
  score: number;
}
// Note: The backend returns recommended roles in two ways:
// 1) A profile-based recommendation from FAISS + re-rank (Role interface)
// 2) A resume-derived recommendation from the documents endpoint (ResumeRole interface)
// The frontend merges these two sources, preferring the immediate context from the upload result but falling back to DB-persisted resume roles for persistence across sessions.
function MatchBar({ score }: { score: number }) {
  // Convert score (0 to 1) to percentage and determine color based on thresholds
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? 'var(--success)' : pct >= 55 ? 'var(--brand-500)' : 'var(--warning)';
  return (
    <div className="mt-3">
      <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
        <span>Match</span>
        <span style={{ color, fontWeight: 600 }}>{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--border-subtle)' }}>
        <div className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: color, transition: 'width 0.6s ease' }} />
      </div>
    </div>
  );
}


export default function RolesPage() {
  const { uploadResult } = useUploadResult();
  const [roles, setRoles] = useState<Role[]>([]);
  // DB-persisted resume roles fetched from the documents endpoint
  const [dbResumeRoles, setDbResumeRoles] = useState<ResumeRole[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      // Profile-based roles from FAISS + re-rank
      api.get<{ roles: Role[] }>('/recommendations/roles/')
        .then((r) => setRoles(r.data.roles || []))
        .catch(() => {}),

      // Most recent document's recommended roles from the DB
      api.get<{ recommended_roles: ResumeRole[] }>('/documents/latest-roles/')
        .then((r) => setDbResumeRoles(r.data.recommended_roles || []))
        .catch(() => {}), // silently ignore if endpoint doesn't exist yet
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
      <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Loading roles…
    </div>
  );

  // Use context roles if available (just uploaded), otherwise fall back to DB
  const contextRoles = uploadResult?.recommended_roles ?? [];
  const fromResume: ResumeRole[] = contextRoles.length > 0 ? contextRoles : dbResumeRoles;

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <h1 style={{ fontFamily: 'var(--font-display)', marginBottom: '0.35rem' }}>Recommended Roles</h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Based on your skills and resume analysis.</p>
      </div>

      {/* Resume-derived roles — persists across logout/login via DB fallback */}
      {fromResume.length > 0 && (
        <section className="anim-fade-up">
          <div className="section-label flex items-center gap-2">
            <span>📄</span> From your resume
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {fromResume.map((r, index) => (
              <div key={`resume-role-${index}`}
                className={`card anim-fade-up delay-${Math.min(index + 1, 5)}`}
                style={{ padding: '1.25rem' }}>
                <h3 className="text-sm font-semibold" style={{ margin: '0 0 0.25rem', color: 'var(--text-primary)' }}>
                  {r.role}
                </h3>
                {r.description && (
                  <p className="text-xs line-clamp-2" style={{ color: 'var(--text-muted)', lineHeight: 1.55 }}>
                    {r.description}
                  </p>
                )}
                {r.skills && (
                  <p className="text-xs mt-2 line-clamp-1" style={{ color: 'var(--brand-400)' }}>
                    {r.skills}
                  </p>
                )}
                {r.score != null && <MatchBar score={r.score} />}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Profile-based roles from FAISS */}
      <section className="anim-fade-up delay-2">
        <div className="section-label flex items-center gap-2">
          <span>👤</span> Based on your profile
        </div>
        {roles.length === 0 ? (
          <div className="surface-alt text-center py-12 rounded-xl" style={{ color: 'var(--text-muted)' }}>
            <p className="text-sm">No role recommendations yet. Add skills or upload your resume to get started.</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {roles.map((r, index) => (
              <div key={r.id}
                className={`card anim-fade-up delay-${Math.min(index + 1, 5)}`}
                style={{ padding: '1.25rem' }}>
                <h3 className="text-sm font-semibold" style={{ margin: '0 0 0.25rem', color: 'var(--text-primary)' }}>
                  {r.title}
                </h3>
                {r.description && (
                  <p className="text-xs line-clamp-2" style={{ color: 'var(--text-muted)', lineHeight: 1.55 }}>
                    {r.description}
                  </p>
                )}
                {r.match_score != null && <MatchBar score={r.match_score} />}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
