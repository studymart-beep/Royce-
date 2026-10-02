"use client";

import { useCallback, useEffect, useState, type ChangeEvent } from "react";
import { Trash2, Upload, FileText, Loader2 } from "lucide-react";
import { getAccessToken } from "@/lib/auth";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

type FileRow = {
  id: string;
  filename: string;
  mime_type?: string;
  size_bytes?: number;
  status: string;
  error_message?: string;
  created_at?: string;
};

export default function FilesPage() {
  const [files, setFiles] = useState<FileRow[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const token = await getAccessToken();
    if (!token) {
      setError("Sign in required");
      return;
    }
    const res = await fetch(`${BACKEND}/files`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      setError("Failed to load files");
      return;
    }
    const data = await res.json();
    setFiles(data.files || []);
    setError(null);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Sign in required");
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${BACKEND}/files`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body?.error?.message || "Upload failed");
      }
      await refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function remove(id: string) {
    const token = await getAccessToken();
    if (!token) return;
    await fetch(`${BACKEND}/files/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    await refresh();
  }

  return (
    <div className="mx-auto max-w-lg px-4 pt-8 pb-12">
      <h1 className="text-xl font-semibold mb-2">Files</h1>
      <p className="text-sm text-slate-muted mb-6">
        Upload PDF, DOCX, TXT, CSV. Royce can search their contents in chat.
      </p>
      <label className="royce-btn-primary inline-flex cursor-pointer mb-6">
        {uploading ? <Loader2 className="animate-spin" size={18} /> : <Upload size={18} />}
        <span>{uploading ? "Processing…" : "Upload file"}</span>
        <input type="file" className="hidden" onChange={(e) => void onUpload(e)} disabled={uploading} />
      </label>
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      <ul className="space-y-2">
        {files.map((f) => (
          <li key={f.id} className="royce-card px-4 py-3 flex items-center gap-3">
            <FileText size={18} className="text-gold-500 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate">{f.filename}</p>
              <p className="text-[11px] text-slate-muted capitalize">
                {f.status}
                {f.size_bytes ? ` · ${(f.size_bytes / 1024).toFixed(1)} KB` : ""}
              </p>
            </div>
            <button type="button" onClick={() => void remove(f.id)} className="text-slate-muted hover:text-red-500" aria-label="Delete">
              <Trash2 size={16} />
            </button>
          </li>
        ))}
      </ul>
      {!error && files.length === 0 && (
        <p className="text-sm text-slate-muted text-center py-8">No files uploaded yet.</p>
      )}
    </div>
  );
}
