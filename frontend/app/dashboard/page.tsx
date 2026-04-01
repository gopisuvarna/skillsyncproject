'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

interface DashboardData {
  skill_distribution: { skill: string }[];
  match_score: number;
  top_roles: { id: string; title: string; match_score: number }[];
  skill_gaps: {
    missing_skills: string[];
    coverage_percent: number;
    learning_priority: { skill_id: string; skill_name: string; importance: number }[];
    per_role: { role_id: string; role_title: string; match_score: number; missing_skills: string[]; coverage_percent: number; learning_priority: { skill_id: string; skill_name: string; importance: number }[] }[];
  };
  learning_plan: { id: string; title: string; provider: string; url: string; matched_skills: string[] }[];
  job_matches: { id: string; title: string; company: string; location: string; url: string; matched_skills: string[] }[];
}

function StatCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="card anim-fade-up" style={{ padding: '1.25rem 1.5rem' }}>
      <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>{label}</p>
      <p className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)', color: color ?? 'var(--brand-500)', margin: 0 }}>{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{sub}</p>}
    </div>
  );
}

function ProgressRing({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  const color = pct >= 75 ? 'var(--success)' : pct >= 50 ? 'var(--brand-500)' : 'var(--warning)';

  return (
    <div className="card anim-fade-up delay-1 flex flex-col items-center justify-center" style={{ padding: '1.5rem', gap: '0.5rem' }}>
      <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Match Score</p>
      <div className="relative w-24 h-24 flex items-center justify-center">
        <svg width="96" height="96" viewBox="0 0 96 96" style={{ transform: 'rotate(-90deg)' }}>
          <circle cx="48" cy="48" r={r} fill="none" stroke="var(--border-subtle)" strokeWidth="7" />
          <circle cx="48" cy="48" r={r} fill="none" stroke={color} strokeWidth="7"
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
        </svg>
        <span className="absolute text-xl font-bold" style={{ fontFamily: 'var(--font-display)', color }}>
          {pct}%
        </span>
      </div>
      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Overall readiness</p>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<DashboardData>('/analytics/dashboard/')
      .then((r) => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
      <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Loading dashboard…
    </div>
  );

  if (!data) return (
    <div className="surface-alt rounded-xl text-center py-16" style={{ color: 'var(--text-muted)' }}>
      <p className="text-3xl mb-3">⚠️</p>
      <p className="text-sm">Unable to load dashboard data. Please try refreshing.</p>
    </div>
  );

  const skillCount = data.skill_distribution.length;
  const gapCount   = data.skill_gaps?.missing_skills?.length ?? 0;
  const coverage   = data.skill_gaps?.coverage_percent ?? 0;

  return (
    <div className="space-y-10">

      {/* Page header */}
      <div className="anim-fade-up">
        <h1 style={{ fontFamily: 'var(--font-display)', marginBottom: '0.25rem' }}>Career Overview</h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Your personalised skill and job readiness snapshot.
        </p>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <ProgressRing score={data.match_score} />
        <StatCard label="Skills Added"   value={String(skillCount)}  sub="in your profile"      color="var(--brand-500)" />
        <StatCard label="Skill Gaps"     value={String(gapCount)}    sub="skills to acquire"    color={gapCount > 0 ? 'var(--warning)' : 'var(--success)'} />
        <StatCard label="Coverage"       value={`${coverage}%`}      sub="of required skills"   color="var(--accent-500)" />
      </div>

      {/* Skills */}
      <section className="anim-fade-up delay-1">
        <div className="flex items-center justify-between mb-3">
          <div className="section-label flex items-center gap-2"><span>🛠</span> Your Skills</div>
          <Link href="/dashboard/skills" className="text-xs font-medium" style={{ color: 'var(--brand-500)' }}>
            Manage →
          </Link>
        </div>
        {skillCount > 0 ? (
          <div className="flex flex-wrap gap-2">
            {data.skill_distribution.map((s, i) => (
              <span key={s.skill} className={`badge badge-brand anim-fade-up`}
                style={{ animationDelay: `${i * 0.025}s` }}>
                {s.skill}
              </span>
            ))}
          </div>
        ) : (
          <div className="surface-alt rounded-xl px-5 py-6 flex items-center gap-4">
            <span className="text-2xl">🌱</span>
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--text-primary)', margin: 0 }}>No skills yet</p>
              <Link href="/dashboard/skills" className="text-xs" style={{ color: 'var(--brand-500)' }}>
                Add your first skill →
              </Link>
            </div>
          </div>
        )}
      </section>

      {/* Top roles */}
      {data.top_roles?.length > 0 && (
        <section className="anim-fade-up delay-2">
          <div className="flex items-center justify-between mb-3">
            <div className="section-label flex items-center gap-2"><span>🗺</span> Top Recommended Roles</div>
            <Link href="/dashboard/roles" className="text-xs font-medium" style={{ color: 'var(--brand-500)' }}>
              View all →
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.top_roles.map((r, i) => {
              const pct = Math.round(r.match_score * 100);
              const barColor = pct >= 75 ? 'var(--success)' : pct >= 50 ? 'var(--brand-500)' : 'var(--warning)';
              return (
                <Link key={r.id} href={`/dashboard/roles?id=${r.id}`}
                  className={`card anim-fade-up delay-${Math.min(i + 2, 5)}`}
                  style={{ padding: '1.1rem 1.25rem', textDecoration: 'none', display: 'block' }}>
                  <h3 className="text-sm font-semibold" style={{ margin: '0 0 0.5rem', color: 'var(--text-primary)' }}>
                    {r.title}
                  </h3>
                  <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                    <span>Match</span>
                    <span style={{ color: barColor, fontWeight: 600 }}>{pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--border-subtle)' }}>
                    <div className="h-full rounded-full"
                      style={{ width: `${pct}%`, background: barColor, transition: 'width 0.6s ease' }} />
                  </div>
                </Link>
              );
            })} 
          </div>
        </section>
      )}

      {/* Skill gaps - per role */}
      {data.skill_gaps?.per_role?.length > 0 && (
        <section className="anim-fade-up delay-2">
          <div className="section-label flex items-center gap-2 mb-3">
            <span>⚡</span> Skill Gaps by Role
            <span className="ml-1 badge" style={{ background: '#fff7ed', color: 'var(--warning)', borderColor: '#fed7aa', fontSize: '0.7rem' }}>
              {gapCount} missing overall
            </span>
          </div>
          <div className="space-y-3">
            {data.skill_gaps.per_role.map((roleGap, ri) => (
              <div key={roleGap.role_id} className={`card anim-fade-up delay-${Math.min(ri + 1, 5)}`} style={{ padding: '1.25rem' }}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-semibold" style={{ margin: 0, color: 'var(--text-primary)' }}>
                    {roleGap.role_title}
                  </h3>
                  <span className="text-xs font-semibold" style={{ color: roleGap.coverage_percent >= 80 ? 'var(--success)' : roleGap.coverage_percent >= 50 ? 'var(--brand-500)' : 'var(--warning)' }}>
                    {roleGap.coverage_percent}% covered
                  </span>
                </div>
                {roleGap.missing_skills.length === 0 ? (
                  <p className="text-xs" style={{ color: 'var(--success)' }}>✓ You have all required skills</p>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {(roleGap.learning_priority?.length
                      ? roleGap.learning_priority
                      : roleGap.missing_skills.map(s => ({ skill_name: s, importance: 0.5 }))
                    ).map((item, i) => {
                      const name = item.skill_name;
                      const imp  = item.importance;
                      const tag  = imp >= 0.8 ? 'High' : imp >= 0.5 ? 'Med' : 'Low';
                      const tagColor = imp >= 0.8 ? '#ef4444' : imp >= 0.5 ? 'var(--warning)' : 'var(--text-muted)';
                      return (
                        <span key={name} className="badge flex items-center gap-1"
                          style={{ background: '#fff7ed', color: 'var(--warning)', borderColor: '#fed7aa', fontSize: '0.7rem' }}>
                          {name}
                          <span style={{ fontSize: '0.6rem', fontWeight: 700, color: tagColor }}>{tag}</span>
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Two-column: learning + jobs */}
      <div className="grid gap-6 lg:grid-cols-2">

        {/* Learning plan */}
        <section className="anim-fade-up delay-3">
          <div className="section-label flex items-center gap-2 mb-3"><span>📚</span> Learning Recommendations</div>
          {data.learning_plan?.length > 0 ? (
            <div className="space-y-2">
              {data.learning_plan.slice(0, 7).map((c) => (
                <a key={c.id} href={c.url} target="_blank" rel="noopener noreferrer"
                  className="card flex items-start gap-3 group"
                  style={{ padding: '0.875rem 1rem', textDecoration: 'none' }}>
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm"
                    style={{ background: 'var(--brand-50)', border: '1.5px solid var(--brand-200)' }}>
                    🎓
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-medium truncate" style={{ margin: 0, color: 'var(--text-primary)' }}>
                      {c.title}
                    </h3>
                    <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-muted)' }}>
                      {c.provider} · {c.matched_skills.join(', ')}
                    </p>
                  </div>
                  <span className="flex-shrink-0 text-xs transition-transform group-hover:translate-x-0.5"
                    style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>→</span>
                </a>
              ))}
            </div>
          ) : (
            <div className="surface-alt rounded-xl text-center py-8" style={{ color: 'var(--text-muted)' }}>
              <p className="text-2xl mb-2">📚</p>
              <p className="text-sm">No course recommendations yet.</p>
              <p className="text-xs mt-1">Add skills or upload your resume to get learning suggestions.</p>
            </div>
          )}
        </section>

        {/* Job matches */}
        {data.job_matches?.length > 0 && (
          <section className="anim-fade-up delay-4">
            <div className="flex items-center justify-between mb-3">
              <div className="section-label flex items-center gap-2"><span>💼</span> Job Matches</div>
              <Link href="/dashboard/jobs" className="text-xs font-medium" style={{ color: 'var(--brand-500)' }}>
                View all →
              </Link>
            </div>
            <div className="space-y-2">
              {data.job_matches.map((j) => (
                <a key={j.id} href={j.url} target="_blank" rel="noopener noreferrer"
                  className="card flex items-start gap-3 group"
                  style={{ padding: '0.875rem 1rem', textDecoration: 'none' }}>
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold"
                    style={{ background: 'var(--accent-100)', color: 'var(--accent-500)', border: '1.5px solid rgba(52,201,174,0.25)' }}>
                    {j.company.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-medium truncate" style={{ margin: 0, color: 'var(--text-primary)' }}>
                      {j.title}
                    </h3>
                    <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-muted)' }}>
                      {j.company}{j.location ? ' · ' + j.location : ''}
                    </p>
                  </div>
                  <span className="flex-shrink-0 text-xs transition-transform group-hover:translate-x-0.5"
                    style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>→</span>
                </a>
              ))}
            </div>
          </section>
        )}

      </div>
    </div>
  );
}

