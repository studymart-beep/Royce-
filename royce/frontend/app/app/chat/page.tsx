"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Send, Plus, MessageSquare, Trash2 } from "lucide-react";
import { api, type ChatResponse } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import { cn } from "@/lib/utils";

type Msg = { role: "user" | "assistant"; content: string; provider?: string };
type Conv = { id: string; title?: string | null; updated_at?: string };

function simpleMarkdown(text: string) {
  // Minimal safe-ish rendering: escape HTML, code fences, bold, inline code
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  html = html.replace(/```([\s\S]*?)```/g, (_m, code) => {
    return `<pre class="bg-ivory-200/80 rounded-xl p-3 overflow-x-auto text-xs my-2"><code>${code.trim()}</code></pre>`;
  });
  html = html.replace(/`([^`]+)`/g, '<code class="bg-ivory-200 px-1 rounded text-xs">$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\n/g, "<br/>");
  return html;
}

function ChatInner() {
  const search = useSearchParams();
  const initialQ = search.get("q") ?? "";
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState(initialQ);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conv[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showList, setShowList] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadConversations = useCallback(async () => {
    const token = await getAccessToken();
    if (!token) return;
    try {
      const res = await api.listConversations(token);
      setConversations((res.conversations as Conv[]) || []);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function openConversation(id: string) {
    const token = await getAccessToken();
    if (!token) return;
    setError(null);
    try {
      const data = await api.getConversation(token, id);
      setConversationId(id);
      const msgs = (data.messages as Array<{ role: string; content?: string; provider?: string }>) || [];
      setMessages(
        msgs
          .filter((m) => m.role === "user" || m.role === "assistant")
          .map((m) => ({
            role: m.role as "user" | "assistant",
            content: m.content || "",
            provider: m.provider,
          }))
      );
      setShowList(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load conversation");
    }
  }

  function newChat() {
    setConversationId(null);
    setMessages([]);
    setError(null);
    setShowList(false);
  }

  async function deleteConv(id: string) {
    const token = await getAccessToken();
    if (!token) return;
    await api.deleteConversation(token, id);
    if (conversationId === id) newChat();
    await loadConversations();
  }

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError(null);
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);
    try {
      const token = await getAccessToken();
      if (!token) {
        setError("Please sign in to chat.");
        setLoading(false);
        return;
      }
      const res: ChatResponse = await api.chat(token, {
        conversation_id: conversationId,
        message: text,
      });
      setConversationId(res.conversation_id);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.content ?? "", provider: res.provider },
      ]);
      void loadConversations();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setLoading(false);
    }
  }, [input, loading, conversationId, loadConversations]);

  return (
    <div className="flex h-[calc(100dvh-4rem)] md:h-[calc(100dvh)] max-w-5xl mx-auto w-full">
      {/* Conversation list — desktop always, mobile toggle */}
      <aside
        className={cn(
          "w-64 border-r border-ivory-300/60 bg-ivory-50/90 flex-col shrink-0",
          showList ? "flex absolute inset-y-0 left-0 z-20 md:relative" : "hidden md:flex"
        )}
      >
        <div className="p-3 border-b border-ivory-300/60">
          <button type="button" onClick={newChat} className="royce-btn-primary w-full text-xs py-2">
            <Plus size={14} /> New chat
          </button>
        </div>
        <ul className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((c) => (
            <li key={c.id} className="group flex items-center gap-1">
              <button
                type="button"
                onClick={() => void openConversation(c.id)}
                className={cn(
                  "flex-1 text-left text-xs px-2 py-2 rounded-xl truncate",
                  conversationId === c.id ? "bg-gold-50 text-gold-600" : "hover:bg-ivory-200/60"
                )}
              >
                {c.title || "Untitled"}
              </button>
              <button
                type="button"
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-muted hover:text-red-500"
                onClick={() => void deleteConv(c.id)}
                aria-label="Delete"
              >
                <Trash2 size={12} />
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center justify-between px-4 py-3 border-b border-ivory-300/60 bg-ivory-50/80 backdrop-blur sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="md:hidden p-1.5 rounded-lg hover:bg-ivory-200"
              onClick={() => setShowList((s) => !s)}
              aria-label="Conversations"
            >
              <MessageSquare size={18} />
            </button>
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-gold-200 to-ivory-300" />
            <div>
              <p className="text-sm font-medium">Royce</p>
              <p className="text-[11px] text-emerald-600">Online</p>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.length === 0 && !loading && (
            <div className="text-center text-slate-muted text-sm mt-16 space-y-2">
              <p className="text-base font-medium text-slate-soft">Start a conversation</p>
              <p>Ask anything — Royce can use tools, memory, and your files.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-soft",
                  m.role === "user"
                    ? "bg-slate-ink text-ivory-50 rounded-br-md"
                    : "bg-ivory-50 border border-ivory-300/60 text-slate-ink rounded-bl-md"
                )}
              >
                {m.role === "assistant" ? (
                  <div dangerouslySetInnerHTML={{ __html: simpleMarkdown(m.content) }} />
                ) : (
                  m.content
                )}
                {m.provider && (
                  <p className="mt-1.5 text-[10px] text-slate-muted">via {m.provider}</p>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-ivory-50 border border-ivory-300/60 rounded-2xl rounded-bl-md px-4 py-3 text-sm text-slate-muted">
                Thinking…
              </div>
            </div>
          )}
          {error && (
            <div className="text-center space-y-2">
              <p className="text-sm text-red-600 bg-red-50 rounded-xl px-3 py-2">{error}</p>
              <button type="button" className="text-xs text-gold-500 font-medium" onClick={() => setError(null)}>
                Dismiss
              </button>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="border-t border-ivory-300/60 bg-ivory-50/95 px-3 py-3 pb-4">
          <div className="flex items-end gap-2">
            <textarea
              className="royce-input flex-1 resize-none min-h-[44px] max-h-32 py-2.5"
              rows={1}
              placeholder="Message Royce…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
            />
            <button
              type="button"
              onClick={() => void send()}
              disabled={loading || !input.trim()}
              className="p-2.5 rounded-full bg-slate-ink text-ivory-50 disabled:opacity-40"
              aria-label="Send"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-slate-muted">Loading chat…</div>}>
      <ChatInner />
    </Suspense>
  );
}
