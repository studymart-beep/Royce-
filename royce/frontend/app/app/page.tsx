"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageCircle, Upload, KeyRound, Calendar, CheckSquare, Brain } from "lucide-react";
import { api } from "@/lib/api";
import { getAccessToken, getUser } from "@/lib/auth";

const quick = [
  { href: "/app/chat", label: "Chat", desc: "Ask anything", icon: MessageCircle, color: "bg-gold-50 text-gold-500" },
  { href: "/app/files", label: "Files", desc: "Upload docs", icon: Upload, color: "bg-violet-50 text-violet-500" },
  { href: "/app/tasks", label: "Tasks", desc: "Plans", icon: Calendar, color: "bg-emerald-50 text-emerald-500" },
  { href: "/app/settings/providers", label: "Providers", desc: "API keys", icon: KeyRound, color: "bg-sky-50 text-sky-500" },
];

export default function HomePage() {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const [name, setName] = useState("");
  const [recent, setRecent] = useState<Array<{ id: string; title?: string | null }>>([]);
  const [taskCount, setTaskCount] = useState(0);
  const [memCount, setMemCount] = useState(0);
  const [providers, setProviders] = useState(0);

  useEffect(() => {
    (async () => {
      const user = await getUser();
      const meta = user?.user_metadata as { full_name?: string } | undefined;
      setName(meta?.full_name || user?.email?.split("@")[0] || "");
      const token = await getAccessToken();
      if (!token) return;
      try {
        const [c, t, m, p] = await Promise.all([
          api.listConversations(token),
          api.listTasks(token),
          api.listMemories(token),
          api.listProviders(token),
        ]);
        setRecent(((c.conversations as Array<{ id: string; title?: string }>) || []).slice(0, 5));
        const tasks = (t.tasks as Array<{ status?: string }>) || [];
        setTaskCount(tasks.filter((x) => x.status !== "done").length);
        setMemCount(((m.memories as unknown[]) || []).length);
        setProviders(((p.providers as unknown[]) || []).length);
      } catch {
        /* backend may be offline */
      }
    })();
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-4 pt-8 md:pt-12 pb-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">
          {greeting}{name ? `, ${name}` : ""}
        </h1>
        <p className="text-slate-soft mt-1 text-sm">How can I help you today?</p>
      </header>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        {quick.map((q) => (
          <Link
            key={q.href}
            href={q.href}
            className="flex flex-col items-center gap-2 rounded-2xl bg-ivory-50 border border-ivory-300/50 p-3 shadow-soft hover:shadow-card transition"
          >
            <span className={`h-10 w-10 rounded-xl flex items-center justify-center ${q.color}`}>
              <q.icon size={20} />
            </span>
            <span className="text-xs font-medium">{q.label}</span>
            <span className="text-[10px] text-slate-muted">{q.desc}</span>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-3 mb-8">
        <div className="royce-card p-3 text-center">
          <CheckSquare size={16} className="mx-auto text-gold-500 mb-1" />
          <p className="text-lg font-semibold">{taskCount}</p>
          <p className="text-[10px] text-slate-muted">Open tasks</p>
        </div>
        <div className="royce-card p-3 text-center">
          <Brain size={16} className="mx-auto text-gold-500 mb-1" />
          <p className="text-lg font-semibold">{memCount}</p>
          <p className="text-[10px] text-slate-muted">Memories</p>
        </div>
        <div className="royce-card p-3 text-center">
          <KeyRound size={16} className="mx-auto text-gold-500 mb-1" />
          <p className="text-lg font-semibold">{providers}</p>
          <p className="text-[10px] text-slate-muted">Providers</p>
        </div>
      </div>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-slate-soft">Recent chats</h2>
          <Link href="/app/chat" className="text-xs text-gold-500">See all</Link>
        </div>
        {recent.length === 0 ? (
          <p className="text-sm text-slate-muted royce-card px-4 py-6 text-center">
            No conversations yet.{" "}
            <Link href="/app/chat" className="text-gold-500 font-medium">Start chatting</Link>
          </p>
        ) : (
          <ul className="space-y-2">
            {recent.map((c) => (
              <li key={c.id}>
                <Link href="/app/chat" className="block royce-card px-4 py-3.5 text-sm hover:border-gold-200 transition truncate">
                  {c.title || "Untitled conversation"}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
