"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Plus, Trash2, Search } from "lucide-react";
import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

type Memory = {
  id: string;
  content: string;
  memory_type?: string;
  importance?: number;
  created_at?: string;
};

export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [q, setQ] = useState("");
  const [newContent, setNewContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (query?: string) => {
    try {
      const token = await getAccessToken();
      if (!token) {
        setError("Sign in required");
        return;
      }
      const res = await api.listMemories(token, query);
      setMemories((res.memories as Memory[]) || []);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function addMemory(e: FormEvent) {
    e.preventDefault();
    if (!newContent.trim()) return;
    const token = await getAccessToken();
    if (!token) return;
    await api.createMemory(token, { content: newContent.trim() });
    setNewContent("");
    await refresh();
  }

  async function remove(id: string) {
    const token = await getAccessToken();
    if (!token) return;
    await api.deleteMemory(token, id);
    await refresh(q || undefined);
  }

  return (
    <div className="mx-auto max-w-lg px-4 pt-8 pb-12">
      <h1 className="text-xl font-semibold mb-2">Memory</h1>
      <p className="text-sm text-slate-muted mb-6">
        Royce remembers to give you a more personal and helpful experience.
      </p>
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-muted" />
        <input
          className="royce-input pl-9"
          placeholder="Search memories…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void refresh(q || undefined);
          }}
        />
      </div>
      <form onSubmit={(e) => void addMemory(e)} className="flex gap-2 mb-6">
        <input
          className="royce-input flex-1"
          placeholder="Add a memory…"
          value={newContent}
          onChange={(e) => setNewContent(e.target.value)}
        />
        <button type="submit" className="royce-btn-primary px-4" aria-label="Add">
          <Plus size={18} />
        </button>
      </form>
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      <ul className="space-y-2">
        {memories.map((m) => (
          <li key={m.id} className="royce-card px-4 py-3 flex gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm">{m.content}</p>
              {m.memory_type && (
                <p className="text-[11px] text-slate-muted mt-1 capitalize">{m.memory_type}</p>
              )}
            </div>
            <button type="button" onClick={() => void remove(m.id)} className="text-slate-muted hover:text-red-500" aria-label="Delete">
              <Trash2 size={16} />
            </button>
          </li>
        ))}
      </ul>
      {!error && memories.length === 0 && (
        <p className="text-sm text-slate-muted text-center py-8">No memories yet.</p>
      )}
    </div>
  );
}
