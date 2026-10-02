# Royce

Personal AI assistant — Next.js + FastAPI + Supabase.

## Stack

- **Frontend:** Next.js (TypeScript, Tailwind) — deploy on **Vercel**
- **Backend:** FastAPI — deploy on **Render**
- **Data / Auth / Storage / pgvector:** Supabase

## Local setup

1. Apply SQL in Supabase SQL Editor (schema + storage migrations).
2. Copy `.env.example` → `.env` (backend) and fill Supabase + `CREDENTIALS_ENCRYPTION_KEY`.
3. Frontend: `frontend/.env.local` with `NEXT_PUBLIC_SUPABASE_*` and `NEXT_PUBLIC_BACKEND_URL`.

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Security

- Never commit `.env` or service role keys.
- AI provider keys are entered in the Royce dashboard and encrypted server-side.
