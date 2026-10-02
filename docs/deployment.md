# Deployment

## Backend (Render)

1. Connect the GitHub repo.
2. Root directory: `backend`
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables (see `.env.example`):
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `CREDENTIALS_ENCRYPTION_KEY` (generate once, keep secret)
   - `CORS_ORIGINS` (your frontend origin)
   - Optional: `WEB_SEARCH_API_KEY`, etc.

## Database

Apply all files in `database/migrations/` in order via the Supabase SQL editor (or Supabase CLI).

## Frontend

Deploy Next.js via Vercel / Netlify / similar Git-based flow.
Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and `BACKEND_URL` / `NEXT_PUBLIC_BACKEND_URL`.

## CORS

Configure `CORS_ORIGINS` on the backend to the exact frontend origin(s).
