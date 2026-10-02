const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {}
): Promise<T> {
  const { token, headers: extraHeaders, ...rest } = options;
  const headers: Record<string, string> = {
    ...(extraHeaders as Record<string, string>),
  };
  if (!(rest.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BACKEND_URL}${path}`, { ...rest, headers });
  if (!res.ok) {
    let body: { error?: { code?: string; message?: string; details?: unknown } } = {};
    try {
      body = await res.json();
    } catch {
      /* ignore */
    }
    throw new ApiError(
      res.status,
      body.error?.code ?? "HTTP_ERROR",
      body.error?.message ?? res.statusText,
      body.error?.details
    );
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type ChatRequest = {
  conversation_id?: string | null;
  message: string;
  model?: string | null;
  provider?: string | null;
  stream?: boolean;
};

export type ChatResponse = {
  conversation_id: string;
  message_id: string;
  role: string;
  content: string | null;
  provider: string;
  model: string;
  tool_calls: unknown[];
  usage?: { input_tokens?: number; output_tokens?: number; total_tokens?: number } | null;
};

export type ProviderView = {
  id?: string;
  provider: string;
  key_hint: string;
  is_enabled: boolean;
  priority: number;
  preferred_model?: string | null;
  last_tested_at?: string | null;
  last_test_status?: string | null;
};

export const api = {
  health: () => request<{ status: string }>("/health"),
  me: (token: string) => request<Record<string, unknown>>("/auth/me", { token }),
  chat: (token: string, body: ChatRequest) =>
    request<ChatResponse>("/chat", { method: "POST", body: JSON.stringify(body), token }),
  listConversations: (token: string) =>
    request<{ conversations: Array<Record<string, unknown>> }>("/conversations", { token }),
  getConversation: (token: string, id: string) =>
    request<Record<string, unknown>>(`/conversations/${id}`, { token }),
  deleteConversation: (token: string, id: string) =>
    request<{ ok: boolean }>(`/conversations/${id}`, { method: "DELETE", token }),
  listTasks: (token: string) => request<{ tasks: Array<Record<string, unknown>> }>("/tasks", { token }),
  createTask: (token: string, body: { title: string; description?: string; due_at?: string }) =>
    request<Record<string, unknown>>("/tasks", { method: "POST", body: JSON.stringify(body), token }),
  updateTask: (token: string, id: string, body: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(body), token }),
  deleteTask: (token: string, id: string) =>
    request<{ ok: boolean }>(`/tasks/${id}`, { method: "DELETE", token }),
  listMemories: (token: string, q?: string) =>
    request<{ memories: Array<Record<string, unknown>> }>(
      q ? `/memories?q=${encodeURIComponent(q)}` : "/memories",
      { token }
    ),
  createMemory: (token: string, body: { content: string; memory_type?: string }) =>
    request<Record<string, unknown>>("/memories", { method: "POST", body: JSON.stringify(body), token }),
  deleteMemory: (token: string, id: string) =>
    request<{ ok: boolean }>(`/memories/${id}`, { method: "DELETE", token }),
  listProviders: (token: string) =>
    request<{ providers: ProviderView[] }>("/providers", { token }),
  upsertProvider: (
    token: string,
    provider: string,
    body: { api_key: string; preferred_model?: string; priority?: number; is_enabled?: boolean }
  ) =>
    request<ProviderView>(`/providers/${provider}`, {
      method: "PUT",
      body: JSON.stringify(body),
      token,
    }),
  deleteProvider: (token: string, provider: string) =>
    request<{ ok: boolean }>(`/providers/${provider}`, { method: "DELETE", token }),
  testProvider: (token: string, provider: string) =>
    request<{ status: string; message?: string; sample?: string }>(`/providers/${provider}/test`, {
      method: "POST",
      token,
    }),
};
