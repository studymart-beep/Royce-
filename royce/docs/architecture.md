# Royce Architecture

## High-level

```
USER (Mobile / Web)
        │
        ▼
┌───────────────────┐
│     Next.js       │  Frontend (TypeScript, Tailwind, Lucide)
│  Royce Frontend   │
└─────────┬─────────┘
          │ HTTPS
          ▼
┌───────────────────┐
│     FastAPI       │  Backend (Python)
│  Royce Backend    │  Hosted on Render
└─────────┬─────────┘
          │
   ┌──────┼──────┐
   ▼      ▼      ▼
AI Router  Memory  Tools
   │      Engine
   │        │
   │        ▼
   │    Supabase
   │    PostgreSQL
   │    + pgvector
   │
   ▼
AI Providers
Gemini · Groq · Cerebras · (extensible)
```

## Design principles

1. **Modular monolith** — clear internal boundaries, single deployable backend.
2. **Provider abstraction** — the rest of the system never imports a concrete provider.
3. **User isolation** — every row has `user_id`; RLS + backend JWT verification.
4. **Context efficiency** — recent messages + retrieved memories + tool results only.
5. **Fail closed** — auth required; no cross-user data leakage.
6. **V1 simplicity** — no Redis, Kafka, K8s, separate vector DB, agent frameworks.

## Backend dependency flow

```
HTTP / API layer
      ↓
Service layer          (chat, tasks, files …)
      ↓
Domain systems         (AI router, memory engine, tool registry)
      ↓
Infrastructure         (Supabase client, provider SDKs, search clients)
```

Business logic lives in services and domain modules, **not** in FastAPI route handlers.

## AI Router

- Abstract `BaseProvider` with `async generate(messages, model=None, tools=None, **kwargs) -> AIResponse`
- Normalized `AIResponse` (content, provider, model, finish_reason, tool_calls, usage, metadata)
- Deterministic selection + ordered fallbacks
- Error classification: auth, invalid request, rate-limit, transient, timeout, unavailable
- Only appropriate errors trigger failover
- Usage persisted to `provider_usage`

## Memory

- Recent conversation window (configurable)
- Long-term memories stored with embeddings in pgvector
- Semantic retrieval always scoped by `user_id`
- Extraction pipeline (not “save every message”)
- Context builder enforces hard token/character limits

## Tools

Registry pattern. Initial tools: `web_search`, `calculator`, `weather`, `memory`, `tasks`, `files`, `date_time`.  
Each tool declares name, description, input schema, and a pure execution function. No arbitrary code execution.

## Database

Supabase PostgreSQL is the permanent application database.  
Render is used only for the FastAPI process.

## Auth

Supabase Auth → JWT → FastAPI verifies identity → all subsequent operations use the verified `user_id`.  
Service role key is used only server-side after identity is established.

## Provider credentials (dashboard-managed)

API keys are **not** stored in backend `.env`.

Flow:

1. User enters key in Royce Settings → Providers
2. FastAPI encrypts with `CREDENTIALS_ENCRYPTION_KEY` (Fernet)
3. Ciphertext + key_hint stored in `provider_credentials` (per user_id)
4. On chat, router resolves credentials for the authenticated user, decrypts server-side, calls provider
5. Raw key is never returned to the browser after storage

RLS ensures User A cannot read User B's credentials.
