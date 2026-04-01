'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useUploadResult } from '../upload-result-context';

interface UserSkill {
  id: string;
  skill_name: string;
  source: string;
}

export default function SkillsPage() {
  const { uploadResult } = useUploadResult();
  const [skills, setSkills] = useState<UserSkill[]>([]);
  const [newSkill, setNewSkill] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadSkills(); }, []);

  function loadSkills() {
    api.get<UserSkill[]>('/skills/')
      .then((r) => setSkills(r.data))
      .catch(() => [])
      .finally(() => setLoading(false));
  }

  async function addSkill(e: React.FormEvent) {
    e.preventDefault();
    if (!newSkill.trim()) return;
    try {
      await api.post('/skills/', { name: newSkill.trim() });
      setNewSkill('');
      loadSkills();
    } catch { /* ignore */ }
  }

  async function removeSkill(id: string) {
    try {
      await api.delete(`/skills/${id}/`);
      loadSkills();
    } catch { /* ignore */ }
  }

  if (loading) return (
    <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
      <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Loading skills…
    </div>
  );

  // Use context skills if available (just uploaded), otherwise fall back to
  // the document-sourced skills already saved in the DB
  const contextSkills = uploadResult?.all_skills ?? [];
  // DB-persisted document skills (not lost on logout/login)
  const dbResumeSkills = skills.filter(s => s.source === 'document').map(s => s.skill_name);
  // Prefer context skills (immediate feedback on upload) but fall back to DB skills for persistence across sessions
  const extractedSkills = contextSkills.length > 0 ? contextSkills : dbResumeSkills;

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Page header */}
      <div>
        <h1 style={{ fontFamily: 'var(--font-display)', marginBottom: '0.35rem' }}>Skills</h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Manage your skill profile to get better job and role matches.
        </p>
      </div>

      {/* Resume-extracted skills — persists across logout/login via DB fallback */}
      {extractedSkills.length > 0 && (
        <div className="card anim-fade-up" style={{ padding: '1.5rem' }}>
          <div className="flex items-center gap-2 mb-4">
            <span className="text-base">📄</span>
            <h2 className="text-base" style={{ margin: 0 }}>Extracted from Resume</h2>
            <span className="ml-auto badge badge-accent">{extractedSkills.length} skills</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {extractedSkills.map((skill, index) => (
              <span key={`resume-${index}`} className="badge badge-brand anim-fade-up"
                style={{ animationDelay: `${index * 0.03}s` }}>
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Manually added skills */}
      <div className="card anim-fade-up delay-1" style={{ padding: '1.5rem' }}>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-base">🛠</span>
          <h2 className="text-base" style={{ margin: 0 }}>Your Skills</h2>
          <span className="ml-auto badge badge-brand">{skills.length}</span>
        </div>

        {/* Add skill form */}
        <form onSubmit={addSkill} className="flex gap-2 mb-5">
          <input
            type="text"
            placeholder="e.g. Python, Project Management…"
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            className="input flex-1"
          />
          <button type="submit" className="btn btn-primary px-5">
            Add
          </button>
        </form>

        {skills.length === 0 ? (
          <p className="text-sm text-center py-4" style={{ color: 'var(--text-muted)' }}>
            No skills added yet. Add your first skill above.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {skills.map((s, i) => (
              <span key={s.id}
                className="inline-flex items-center gap-1.5 anim-fade-up"
                style={{
                  padding: '0.3rem 0.75rem 0.3rem 0.9rem',
                  borderRadius: 'var(--radius-full)',
                  background: 'var(--bg-surface-alt)',
                  border: '1.5px solid var(--border-medium)',
                  fontSize: '0.8125rem',
                  fontWeight: 500,
                  color: 'var(--text-primary)',
                  animationDelay: `${i * 0.03}s`,
                }}>
                {s.skill_name}
                <button
                  onClick={() => removeSkill(s.id)}
                  aria-label={`Remove ${s.skill_name}`}
                  className="flex items-center justify-center w-4 h-4 rounded-full transition-all text-xs"
                  style={{ color: 'var(--text-muted)' }}
                  onMouseOver={e => (e.currentTarget.style.color = 'var(--error)')}
                  onMouseOut={e => (e.currentTarget.style.color = 'var(--text-muted)')}>
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

