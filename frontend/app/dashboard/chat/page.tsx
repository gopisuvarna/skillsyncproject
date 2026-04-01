   'use client';
//Auto scrolling chat to bottom-useref refer DOM element and scrollIntoView method to scroll to bottom when messages change
import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// ── Markdown renderer ─────────────────────────────────────────────
// Renders assistant messages: headings, bold, bullets, numbered lists, links, code
function MarkdownMessage({ content }: { content: string }) {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;

  function renderInline(text: string): React.ReactNode {
    const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g)
      .filter((p): p is string => p !== undefined && p !== null);
    return parts.map((part, idx) => {
      if (!part) return null;
      if (part.startsWith('**') && part.endsWith('**'))
        return <strong key={idx} style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
      if (part.startsWith('`') && part.endsWith('`'))
        return <code key={idx} style={{ background: 'var(--bg-surface-alt)', borderRadius: '4px', padding: '1px 5px', fontSize: '0.8rem', fontFamily: 'monospace' }}>{part.slice(1, -1)}</code>;
      const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (linkMatch)
        return <a key={idx} href={linkMatch[2]} target="_blank" rel="noopener noreferrer"
          style={{ color: 'var(--brand-500)', textDecoration: 'underline', wordBreak: 'break-word' }}>{linkMatch[1]}</a>;
      return part;
    });
  }

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      elements.push(<div key={`sp-${i}`} style={{ height: '0.35rem' }} />);
      i++; continue;
    }

    // H1
    if (trimmed.startsWith('# ')) {
      elements.push(
        <h2 key={i} style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 700, margin: '0.8rem 0 0.3rem', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.25rem' }}>
          {renderInline(trimmed.slice(2))}
        </h2>
      ); i++; continue;
    }

    // H2
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3 key={i} style={{ fontSize: '0.75rem', fontWeight: 700, margin: '0.7rem 0 0.2rem', color: 'var(--brand-500)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {renderInline(trimmed.slice(3))}
        </h3>
      ); i++; continue;
    }

    // H3
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4 key={i} style={{ fontSize: '0.875rem', fontWeight: 600, margin: '0.5rem 0 0.15rem', color: 'var(--text-primary)' }}>
          {renderInline(trimmed.slice(4))}
        </h4>
      ); i++; continue;
    }

    // Section divider ===... or ---...
    if (trimmed.match(/^[=\-]{3,}$/) && trimmed.replace(/[=-]/g, '').length === 0) {
      elements.push(<hr key={i} style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '0.4rem 0' }} />);
      i++; continue;
    }

    // Bullet list — collect consecutive
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      const items: string[] = [];
      while (i < lines.length && (lines[i].trim().startsWith('* ') || lines[i].trim().startsWith('- '))) {
        items.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} style={{ margin: '0.2rem 0', padding: 0, listStyle: 'none' }}>
          {items.map((item, idx) => (
            <li key={idx} style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.18rem', alignItems: 'flex-start' }}>
              <span style={{ color: 'var(--brand-400)', flexShrink: 0, marginTop: '0.15rem' }}>•</span>
              <span style={{ color: 'var(--text-secondary)', lineHeight: 1.55 }}>{renderInline(item)}</span>
            </li>
          ))}
        </ul>
      ); continue;
    }

    // Numbered list — collect consecutive
    if (trimmed.match(/^\d+[.)]\s/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].trim().match(/^\d+[.)]\s/)) {
        items.push(lines[i].trim().replace(/^\d+[.)]\s/, ''));
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} style={{ margin: '0.2rem 0', padding: 0, listStyle: 'none' }}>
          {items.map((item, idx) => (
            <li key={idx} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.18rem', alignItems: 'flex-start' }}>
              <span style={{ color: 'var(--brand-400)', fontWeight: 600, flexShrink: 0, minWidth: '1rem' }}>{idx + 1}.</span>
              <span style={{ color: 'var(--text-secondary)', lineHeight: 1.55 }}>{renderInline(item)}</span>
            </li>
          ))}
        </ol>
      ); continue;
    }

    // Indented sub-bullet
    if (line.match(/^\s{2,}[*\-]\s/)) {
      elements.push(
        <li key={i} style={{ display: 'flex', gap: '0.4rem', marginLeft: '1.4rem', marginBottom: '0.15rem', listStyle: 'none', alignItems: 'flex-start' }}>
          <span style={{ color: 'var(--accent-400)', flexShrink: 0 }}>→</span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', lineHeight: 1.5 }}>{renderInline(trimmed.slice(2))}</span>
        </li>
      ); i++; continue;
    }

    // Plain text
    elements.push(
      <p key={i} style={{ margin: '0.1rem 0', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
        {renderInline(trimmed)}
      </p>
    );
    i++;
  }

  return <div style={{ fontSize: '0.875rem' }}>{elements}</div>;
}


// ── Chat page ─────────────────────────────────────────────────────
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: 'user', content: input.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const msgs = [...messages, userMsg].map((m) => ({ role: m.role, content: m.content }));
      const res = await api.post<{ message: string }>('/chatbot/', { messages: msgs });
      setMessages((m) => [...m, { role: 'assistant', content: res.data.message }]);
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: 'Sorry, I could not respond.' }]);
    } finally {
      setLoading(false);
    }
  }

  const suggestions = [
    'What skills am I missing for my top role?',
    'Give me a learning roadmap for Docker',
    'How ready am I for a Data Scientist role?',
    'What should I learn next?',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] max-w-3xl mx-auto">

      {/* Header */}
      <div className="flex items-center gap-3 pb-4 mb-4" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-sm"
          style={{ background: 'linear-gradient(135deg, var(--brand-500), var(--accent-400))' }}>
          ✦
        </div>
        <div>
          <h1 className="text-lg" style={{ fontFamily: 'var(--font-display)', margin: 0 }}>AI Career Mentor</h1>
          <p className="text-xs" style={{ color: 'var(--text-muted)', margin: 0 }}>Ask about skills, paths, or job readiness</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5 text-xs" style={{ color: 'var(--accent-500)' }}>
          <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: 'var(--accent-400)' }} />
          Online
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 pb-8">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl"
              style={{ background: 'var(--brand-50)', border: '1.5px solid var(--brand-200)' }}>
              🤖
            </div>
            <p className="text-center text-sm" style={{ color: 'var(--text-muted)', maxWidth: '22rem' }}>
              Hi! I'm your AI Career Mentor. Ask me about skill gaps, career transitions, job readiness, or anything career-related.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-sm mt-2">
              {suggestions.map((q) => (
                <button key={q} onClick={() => setInput(q)}
                  className="text-xs text-left px-3 py-2.5 rounded-lg transition-all"
                  style={{ background: 'var(--bg-surface)', border: '1.5px solid var(--border-medium)', color: 'var(--text-secondary)' }}
                  onMouseOver={e => (e.currentTarget.style.borderColor = 'var(--brand-300)')}
                  onMouseOut={e => (e.currentTarget.style.borderColor = 'var(--border-medium)')}>
                  "{q}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex gap-3 anim-fade-up ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* Avatar */}
              <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold"
                style={{
                  background: m.role === 'user'
                    ? 'linear-gradient(135deg, var(--brand-500), var(--accent-400))'
                    : 'var(--bg-surface-alt)',
                  border: m.role === 'assistant' ? '1.5px solid var(--border-medium)' : 'none',
                  color: m.role === 'assistant' ? 'var(--text-muted)' : 'white',
                  marginTop: '2px',
                }}>
                {m.role === 'user' ? 'U' : '✦'}
              </div>

              {/* Bubble */}
              <div className={m.role === 'user' ? 'max-w-[78%] sm:max-w-[70%]' : 'max-w-[90%] sm:max-w-[85%]'}>
                <div className="rounded-2xl"
                  style={m.role === 'user' ? {
                    background: 'var(--brand-500)',
                    color: 'white',
                    fontSize: '0.875rem',
                    lineHeight: 1.6,
                    padding: '0.65rem 1rem',
                    borderBottomRightRadius: '4px',
                  } : {
                    background: 'var(--bg-surface)',
                    border: '1.5px solid var(--border-subtle)',
                    borderBottomLeftRadius: '4px',
                    boxShadow: 'var(--shadow-xs)',
                    padding: '0.875rem 1.1rem',
                  }}>
                  {m.role === 'user'
                    ? m.content
                    : <MarkdownMessage content={m.content} />
                  }
                </div>
              </div>
            </div>
          ))
        )}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3 anim-fade-in">
            <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs"
              style={{ background: 'var(--bg-surface-alt)', border: '1.5px solid var(--border-medium)', color: 'var(--text-muted)', marginTop: '2px' }}>
              ✦
            </div>
            <div className="rounded-2xl px-4 py-3"
              style={{ background: 'var(--bg-surface)', border: '1.5px solid var(--border-subtle)', borderBottomLeftRadius: '4px' }}>
              <span className="flex gap-1 items-center">
                {[0, 1, 2].map(j => (
                  <span key={j} className="w-1.5 h-1.5 rounded-full inline-block"
                    style={{ background: 'var(--text-muted)', animation: `bounce 1s ${j * 0.2}s infinite` }} />
                ))}
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={send} className="flex gap-2 mt-4 pt-4" style={{ borderTop: '1px solid var(--border-subtle)' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything about your career…"
          disabled={loading}
          className="input flex-1"
        />
        <button type="submit" disabled={loading || !input.trim()} className="btn btn-primary px-5">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </form>

      <style>{`
        @keyframes bounce {
          0%, 100% { opacity: 0.3; transform: translateY(0); }
          50%       { opacity: 1;   transform: translateY(-3px); }
        }
      `}</style>
    </div>
  );
}










