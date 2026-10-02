"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Check, Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

type Task = {
  id: string;
  title: string;
  description?: string | null;
  status: string;
  due_at?: string | null;
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const token = await getAccessToken();
      if (!token) {
        setError("Sign in required");
        return;
      }
      const res = await api.listTasks(token);
      setTasks((res.tasks as Task[]) || []);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function addTask(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    const token = await getAccessToken();
    if (!token) return;
    await api.createTask(token, { title: title.trim() });
    setTitle("");
    await refresh();
  }

  async function complete(id: string) {
    const token = await getAccessToken();
    if (!token) return;
    await api.updateTask(token, id, { status: "done" });
    await refresh();
  }

  async function remove(id: string) {
    const token = await getAccessToken();
    if (!token) return;
    await api.deleteTask(token, id);
    await refresh();
  }

  return (
    <div className="mx-auto max-w-lg px-4 pt-8 pb-12">
      <h1 className="text-xl font-semibold mb-6">Tasks</h1>
      <form onSubmit={(e) => void addTask(e)} className="flex gap-2 mb-6">
        <input
          className="royce-input flex-1"
          placeholder="Add a task…"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <button type="submit" className="royce-btn-primary px-4" aria-label="Add">
          <Plus size={18} />
        </button>
      </form>
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-muted">Loading…</p>
      ) : tasks.length === 0 ? (
        <p className="text-sm text-slate-muted">No tasks yet.</p>
      ) : (
        <ul className="space-y-2">
          {tasks.map((t) => (
            <li key={t.id} className="royce-card px-4 py-3 flex items-center gap-3">
              <button
                type="button"
                onClick={() => void complete(t.id)}
                className={`h-6 w-6 rounded-full border flex items-center justify-center shrink-0 ${
                  t.status === "done" ? "bg-emerald-500 border-emerald-500 text-white" : "border-ivory-300"
                }`}
                aria-label="Complete"
              >
                {t.status === "done" && <Check size={14} />}
              </button>
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${t.status === "done" ? "line-through text-slate-muted" : ""}`}>
                  {t.title}
                </p>
              </div>
              <button type="button" onClick={() => void remove(t.id)} className="text-slate-muted hover:text-red-500" aria-label="Delete">
                <Trash2 size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
