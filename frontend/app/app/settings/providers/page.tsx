"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Circle, Loader2 } from "lucide-react";
import { api, type ProviderView } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const CATALOG = [
  { id: "gemini", name: "Gemini", defaultModel: "gemini-2.0-flash" },
  { id: "groq", name: "Groq", defaultModel: "llama-3.3-70b-versatile" },
  { id: "cerebras", name: "Cerebras", defaultModel: "llama3.1-8b" },
];

export default function ProvidersSettingsPage() {
  const [rows, setRows] = useState<ProviderView[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<string | null>(null);
  const [keyInput, setKeyInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const token = await getAccessToken();
    if (!token) {
      setError("Sign in required");
      setLoading(false);
      return;
    }
    try {
      const res = await api.listProviders(token);
      setRows(res.providers || []);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load providers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function viewFor(id: string): ProviderView | undefined {
    return rows.find((r) => r.provider === id);
  }

  async function saveKey(providerId: string) {
    if (!keyInput.trim()) return;
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Sign in required");
      const cat = CATALOG.find((c) => c.id === providerId);
      await api.upsertProvider(token, providerId, {
        api_key: keyInput.trim(),
        preferred_model: cat?.defaultModel,
        priority: providerId === "gemini" ? 10 : providerId === "groq" ? 20 : 30,
        is_enabled: true,
      });
      setEditing(null);
      setKeyInput("");
      setMessage("API key saved securely (encrypted).");
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function testConn(providerId: string) {
    setTesting(providerId);
    setMessage(null);
    setError(null);
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Sign in required");
      const res = await api.testProvider(token, providerId);
      if (res.status === "ok") {
        setMessage(`${providerId}: connected — ${res.sample ?? "ok"}`);
      } else {
        setError(`${providerId}: ${res.message ?? res.status}`);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Test failed");
    } finally {
      setTesting(null);
    }
  }

  async function removeKey(providerId: string) {
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Sign in required");
      await api.deleteProvider(token, providerId);
      setMessage("Key removed");
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <div className="mx-auto max-w-lg px-4 pt-6 pb-12">
      <Link href="/app/settings" className="inline-flex items-center gap-1 text-sm text-slate-soft mb-4">
        <ArrowLeft size={16} /> Settings
      </Link>
      <h1 className="text-xl font-semibold mb-1">AI Providers</h1>
      <p className="text-sm text-slate-muted mb-6">
        Keys are encrypted server-side. The full key is never shown again after save.
      </p>
      {message && <p className="mb-4 text-xs bg-emerald-50 text-emerald-700 rounded-xl px-3 py-2">{message}</p>}
      {error && <p className="mb-4 text-xs bg-red-50 text-red-600 rounded-xl px-3 py-2">{error}</p>}
      {loading ? (
        <div className="flex justify-center py-12 text-slate-muted">
          <Loader2 className="animate-spin" />
        </div>
      ) : (
        <ul className="space-y-3">
          {CATALOG.map((cat) => {
            const p = viewFor(cat.id);
            const hasKey = Boolean(p?.key_hint);
            return (
              <li key={cat.id} className="royce-card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-medium text-sm">{cat.name}</h2>
                      {hasKey ? (
                        <CheckCircle2 size={14} className="text-emerald-500" />
                      ) : (
                        <Circle size={14} className="text-slate-muted" />
                      )}
                    </div>
                    <p className="text-xs text-slate-muted mt-0.5">
                      Model: {p?.preferred_model ?? cat.defaultModel}
                      {p ? ` · Priority: ${p.priority}` : ""}
                    </p>
                    <p className="text-xs mt-1 font-mono text-slate-soft">
                      {p?.key_hint ?? "No API key"}
                    </p>
                  </div>
                </div>
                {editing === cat.id ? (
                  <div className="mt-3 space-y-2">
                    <input
                      type="password"
                      className="royce-input text-sm"
                      placeholder="Paste API key…"
                      value={keyInput}
                      onChange={(e) => setKeyInput(e.target.value)}
                      autoComplete="off"
                    />
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        className="royce-btn-primary text-xs py-2 px-4"
                        disabled={saving || !keyInput.trim()}
                        onClick={() => void saveKey(cat.id)}
                      >
                        {saving ? "Saving…" : "Save key"}
                      </button>
                      <button
                        type="button"
                        className="royce-btn-secondary text-xs py-2 px-4"
                        onClick={() => {
                          setEditing(null);
                          setKeyInput("");
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 flex flex-wrap gap-3">
                    <button
                      type="button"
                      className="text-xs font-medium text-gold-500 hover:text-gold-600"
                      onClick={() => setEditing(cat.id)}
                    >
                      {hasKey ? "Replace API key" : "Add API key"}
                    </button>
                    {hasKey && (
                      <>
                        <button
                          type="button"
                          className="text-xs font-medium text-slate-soft hover:text-slate-ink"
                          disabled={testing === cat.id}
                          onClick={() => void testConn(cat.id)}
                        >
                          {testing === cat.id ? "Testing…" : "Test connection"}
                        </button>
                        <button
                          type="button"
                          className="text-xs font-medium text-red-500 hover:text-red-600"
                          onClick={() => void removeKey(cat.id)}
                        >
                          Remove
                        </button>
                      </>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
