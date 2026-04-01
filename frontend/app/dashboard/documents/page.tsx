"use client";

import { useState } from "react";
import Link from "next/link";
import { useUploadResult } from "../upload-result-context";
import { api } from "@/lib/api";

export default function DocumentsPage() {
  const { setUploadResult } = useUploadResult();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [success, setSuccess] = useState<boolean>(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const chosen = e.target.files?.[0];
    if (!chosen) return;

    if (!chosen.name.toLowerCase().endsWith(".pdf")) {
      setMessage("Please select a PDF file only.");
      setFile(null);
      return;
    }
    setFile(chosen);
    setMessage("");
    setSuccess(false);
  };

  const handleUpload = async () => {
    if (!file) { setMessage("Please select a PDF file."); return; }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("Uploading & extracting skills…");

      // Use the shared api instance (has auto-refresh interceptor on 401)
      // Override Content-Type so axios sets multipart/form-data with correct boundary
      const response = await api.post("/documents/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const data = response.data;

      // Store in context for Skills / Roles pages to read in the same session
      setUploadResult({
        all_skills: data.all_skills || [],
        rule_based_skills: data.rule_based_skills || [],
        llm_skills: data.llm_skills || [],
        recommended_roles: data.recommended_roles || [],
      });

      setMessage("Upload successful! Skills and roles have been extracted.");
      setSuccess(true);
    } catch (error: unknown) {
      const err = error as { response?: { data?: { error?: string } } };
      setMessage(err.response?.data?.error || "Upload failed. Please try again.");
      setSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Page header */}
      <div className="mb-8">
        <h1 style={{ fontFamily: 'var(--font-display)', marginBottom: '0.35rem' }}>Upload Resume</h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          PDF format only — we'll extract your skills and suggest matching roles.
        </p>
      </div>

      <div className="card" style={{ padding: '2rem' }}>
        {/* Drop zone */}
        <label
          htmlFor="resume-upload"
          className="flex flex-col items-center justify-center gap-3 w-full rounded-xl py-10 px-6 cursor-pointer transition-all"
          style={{
            border: '2px dashed var(--border-medium)',
            background: file ? 'var(--brand-50)' : 'var(--bg-surface-alt)',
            borderColor: file ? 'var(--brand-400)' : 'var(--border-medium)',
          }}
          onMouseOver={e => !file && (e.currentTarget.style.borderColor = 'var(--brand-300)')}
          onMouseOut={e => !file && (e.currentTarget.style.borderColor = 'var(--border-medium)')}
        >
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
            style={{ background: file ? 'var(--brand-100)' : 'var(--bg-surface)', border: '1.5px solid var(--border-subtle)' }}
          >
            {file ? '📄' : '☁️'}
          </div>

          {file ? (
            <>
              <p className="font-medium text-sm" style={{ color: 'var(--brand-600)' }}>{file.name}</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {(file.size / 1024).toFixed(1)} KB · Click to change
              </p>
            </>
          ) : (
            <>
              <p className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                Click to browse or drag & drop
              </p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>PDF files only</p>
            </>
          )}

          <input
            id="resume-upload"
            type="file"
            accept="application/pdf,.pdf"
            onChange={handleFileChange}
            className="sr-only"
          />
        </label>

        {/* Upload button */}
        <button
          onClick={handleUpload}
          disabled={loading || !file}
          className="btn btn-primary w-full mt-5"
        >
          {loading ? (
            <>
              <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processing…
            </>
          ) : 'Upload & Extract Skills'}
        </button>

        {/* Status message */}
        {message && (
          <div
            className="mt-4 px-4 py-3 rounded-lg text-sm"
            style={{
              background: success ? '#f0fdf4' : '#fef2f2',
              color: success ? 'var(--success)' : 'var(--error)',
              border: `1px solid ${success ? '#bbf7d0' : '#fca5a5'}`,
            }}
          >
            {message}
          </div>
        )}

        {/* Quick nav links after success */}
        {success && (
          <div className="mt-5 pt-4 flex flex-col sm:flex-row gap-3" style={{ borderTop: '1px solid var(--border-subtle)' }}>
            <Link href="/dashboard/skills" className="btn btn-secondary flex-1 justify-center text-sm">
              View Extracted Skills →
            </Link>
            <Link href="/dashboard/roles" className="btn btn-secondary flex-1 justify-center text-sm">
              View Recommended Roles →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}