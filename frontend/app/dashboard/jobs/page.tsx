'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { api } from '@/lib/api';

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  salary_min: number | null;
  salary_max: number | null;
  skills: string[];
  matched_skills: string[];
  posted_at: string;
}

interface Stats {
  total_jobs: number;
  matched_count: number;
  last_synced: string | null;
}

interface JobsResponse {
  results: Job[];
  total: number;
}

// ── helpers ─────────────────────────────────────────────────────────────────

function formatSalary(min: number | null, max: number | null): string | null {
  if (!min && !max) return null;
  const fmt = (n: number) =>
    n >= 100_000 ? `₹${(n / 100_000).toFixed(0)}L` : `₹${(n / 1000).toFixed(0)}K`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  return `Up to ${fmt(max!)}`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const h = Math.floor(diff / 3_600_000);
  if (h < 1) return 'Just now';
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d === 1) return 'Yesterday';
  if (d < 30) return `${d}d ago`;
  return `${Math.floor(d / 30)}mo ago`;
}

// ── JobCard ──────────────────────────────────────────────────────────────────

function JobCard({ job, showMatch }: { job: Job; showMatch?: boolean }) {
  const salary = formatSalary(job.salary_min, job.salary_max);
  const matchPct = showMatch && job.skills.length > 0
    ? Math.round((job.matched_skills.length / job.skills.length) * 100)
    : null;

  return (
    <a
      href={job.url}
      target="_blank"
      rel="noopener noreferrer"
      className="card group flex items-start gap-4"
      style={{ padding: '1rem 1.25rem', textDecoration: 'none', display: 'flex' }}
    >
      {/* Avatar */}
      <div
        className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold"
        style={{ background: 'var(--brand-50)', border: '1.5px solid var(--brand-200)', color: 'var(--brand-600)' }}
      >
        {(job.company || '?').slice(0, 2).toUpperCase()}
      </div>

      <div className="flex-1 min-w-0">
        {/* Title row */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-semibold" style={{ margin: 0, color: 'var(--text-primary)' }}>
            {job.title}
          </h3>
          <span className="flex-shrink-0 text-sm transition-transform group-hover:translate-x-0.5"
            style={{ color: 'var(--text-muted)', marginTop: '2px' }}>→</span>
        </div>

        {/* Meta row */}
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
          {job.company}
          {job.location ? ` · ${job.location}` : ''}
          {salary ? (
            <span className="ml-2 px-1.5 py-0.5 rounded text-xs font-medium"
              style={{ background: 'var(--success-bg, #EAF3DE)', color: 'var(--success, #3B6D11)' }}>
              {salary}
            </span>
          ) : null}
          <span className="ml-2" style={{ color: 'var(--border-subtle)' }}>·</span>
          <span className="ml-2">{timeAgo(job.posted_at)}</span>
        </p>

        {/* Match bar */}
        {showMatch && matchPct !== null && (
          <div className="mt-2">
            <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
              <span>Skill match</span>
              <span style={{
                fontWeight: 600,
                color: matchPct >= 70 ? 'var(--success)' : matchPct >= 40 ? 'var(--brand-500)' : 'var(--warning)'
              }}>{matchPct}%</span>
            </div>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--border-subtle)' }}>
              <div className="h-full rounded-full"
                style={{
                  width: `${matchPct}%`,
                  background: matchPct >= 70 ? 'var(--success)' : matchPct >= 40 ? 'var(--brand-500)' : 'var(--warning)',
                  transition: 'width 0.6s ease',
                }} />
            </div>
          </div>
        )}

        {/* Skill chips */}
        {showMatch && job.matched_skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {job.matched_skills.slice(0, 5).map((s) => (
              <span key={s} className="badge badge-accent" style={{ fontSize: '0.68rem', padding: '0.1rem 0.45rem' }}>{s}</span>
            ))}
            {job.matched_skills.length > 5 && (
              <span className="badge badge-brand" style={{ fontSize: '0.68rem', padding: '0.1rem 0.45rem' }}>
                +{job.matched_skills.length - 5}
              </span>
            )}
          </div>
        )}
      </div>
    </a>
  );
}

// ── SearchBar ─────────────────────────────────────────────────────────────────

function SearchBar({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm" style={{ color: 'var(--text-muted)' }}>🔍</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search by title or company…"
        className="w-full rounded-xl text-sm"
        style={{
          paddingLeft: '2.25rem',
          paddingRight: '1rem',
          paddingTop: '0.55rem',
          paddingBottom: '0.55rem',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          color: 'var(--text-primary)',
          outline: 'none',
        }}
      />
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

const PER_PAGE = 15;

export default function JobsPage() {
  const [matched, setMatched]     = useState<Job[]>([]);
  const [allJobs, setAllJobs]     = useState<Job[]>([]);
  const [stats, setStats]         = useState<Stats | null>(null);
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch]       = useState('');
  const [page, setPage]           = useState(1);
  const [total, setTotal]         = useState(0);
  const [tab, setTab]             = useState<'matched' | 'all'>('matched');

  const fetchData = useCallback(async (q = search, pg = page) => {
    try {
      const params = new URLSearchParams({ page: String(pg), per_page: String(PER_PAGE) });
      if (q) params.set('q', q);

      const [matchedRes, allRes, statsRes] = await Promise.all([
        api.get<JobsResponse>(`/jobs/matched/?${q ? `q=${encodeURIComponent(q)}` : ''}`),
        api.get<JobsResponse>(`/jobs/?${params.toString()}`),
        api.get<Stats>('/jobs/stats/'),
      ]);

      setMatched(matchedRes.data.results || []);
      setAllJobs(allRes.data.results || []);
      setTotal(allRes.data.total || 0);
      setStats(statsRes.data);
    } catch {
      // silently fail — existing state stays visible
    }
  }, [search, page]);

  // Initial load only
  useEffect(() => {
    setLoading(true);
    fetchData().finally(() => setLoading(false));
  }, []);

  // Search debounce — skip on first render (search starts empty)
  const isFirstRender = useRef(true);
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    const t = setTimeout(() => {
      setPage(1);
      fetchData(search, 1);
    }, 350);
    return () => clearTimeout(t);
  }, [search]);

  // Page change — skip on initial mount
  const isFirstPage = useRef(true);
  useEffect(() => {
    if (isFirstPage.current) {
      isFirstPage.current = false;
      return;
    }
    fetchData(search, page);
  }, [page]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData(search, page);
    setRefreshing(false);
  };

  const totalPages = Math.ceil(total / PER_PAGE);
  const displayJobs = tab === 'matched' ? matched : allJobs;

  return (
    <div className="space-y-6 max-w-3xl">

      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 style={{ fontFamily: 'var(--font-display)', marginBottom: '0.25rem' }}>Jobs</h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {stats ? (
              <>
                <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{stats.total_jobs.toLocaleString()}</span> open positions
                {stats.matched_count > 0 && (
                  <> · <span className="font-medium" style={{ color: 'var(--brand-500)' }}>{stats.matched_count}</span> match your skills</>
                )}
                {stats.last_synced && (
                  <> · Updated {timeAgo(stats.last_synced)}</>
                )}
              </>
            ) : 'Curated for your skill profile.'}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-muted)',
            cursor: refreshing ? 'wait' : 'pointer',
            opacity: refreshing ? 0.6 : 1,
          }}
        >
          <span style={{ display: 'inline-block', animation: refreshing ? 'spin 1s linear infinite' : 'none' }}>↻</span>
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {/* ── Search ────────────────────────────────────────────── */}
      <SearchBar value={search} onChange={setSearch} />

      {/* ── Tabs ──────────────────────────────────────────────── */}
      <div className="flex gap-2">
        {(['matched', 'all'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="text-sm px-4 py-1.5 rounded-lg font-medium"
            style={{
              background: tab === t ? 'var(--brand-500)' : 'var(--bg-surface)',
              color: tab === t ? '#fff' : 'var(--text-muted)',
              border: tab === t ? 'none' : '1px solid var(--border-subtle)',
              cursor: 'pointer',
            }}
          >
            {t === 'matched' ? `✦ Matched (${matched.length})` : `All jobs (${total})`}
          </button>
        ))}
      </div>

      {/* ── Job list ──────────────────────────────────────────── */}
      {loading ? (
        <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
          <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading jobs…
        </div>
      ) : displayJobs.length === 0 ? (
        <div className="surface-alt rounded-xl text-center py-14">
          <p className="text-3xl mb-3">💼</p>
          <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
            {tab === 'matched' ? 'No matched jobs yet' : 'No jobs found'}
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
            {tab === 'matched'
              ? 'Upload your resume or add skills to see matches.'
              : search ? 'Try a different search term.' : 'Jobs will appear after the next sync.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayJobs.map((j, i) => (
            <div key={j.id} className={`anim-fade-up delay-${Math.min(i + 1, 5)}`}>
              <JobCard job={j} showMatch={tab === 'matched'} />
            </div>
          ))}
        </div>
      )}

      {/* ── Pagination (all jobs tab only) ────────────────────── */}
      {tab === 'all' && totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="text-xs px-3 py-1.5 rounded-lg"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: page === 1 ? 'var(--border-subtle)' : 'var(--text-primary)',
              cursor: page === 1 ? 'default' : 'pointer',
            }}
          >← Prev</button>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="text-xs px-3 py-1.5 rounded-lg"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: page === totalPages ? 'var(--border-subtle)' : 'var(--text-primary)',
              cursor: page === totalPages ? 'default' : 'pointer',
            }}
          >Next →</button>
        </div>
      )}

    </div>
  );
}