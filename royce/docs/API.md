# Royce API Contract (V1)

Base URL: `https://<backend-host>` (local: `http://localhost:8000`)

All authenticated endpoints require:

```
Authorization: Bearer <supabase_access_token>
```

Errors follow a consistent shape:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Common status codes: 200, 201, 400, 401, 403, 404, 422, 429, 500.

---

## Health

### `GET /health`
Public. Returns `{ "status": "ok", "service": "royce-backend" }`.

---

## Auth

Authentication is handled by Supabase Auth on the frontend.  
The backend only **verifies** the JWT and extracts `user_id`.

No custom `/auth/login` or `/auth/register` endpoints are required in V1.

Optional:
- `GET /auth/me` → returns the authenticated profile.

---

## Chat

### `POST /chat`
Primary endpoint.

**Request**
```json
{
  "conversation_id": "uuid | null",   // null = create new conversation
  "message": "string",
  "model": "string | null",
  "provider": "string | null",
  "stream": false
}
```

**Response** (non-streaming)
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "role": "assistant",
  "content": "string",
  "provider": "gemini",
  "model": "gemini-2.0-flash",
  "tool_calls": [],
  "usage": {
    "input_tokens": 120,
    "output_tokens": 45,
    "total_tokens": 165
  }
}
```

Streaming (when `stream: true`) uses Server-Sent Events. Exact event shape to be finalized in implementation.

---

## Conversations

- `GET /conversations` — list (paginated)
- `GET /conversations/{id}` — detail + recent messages
- `PATCH /conversations/{id}` — update title etc.
- `DELETE /conversations/{id}`

---

## Memories

- `GET /memories` — list / search
- `POST /memories` — manual create
- `PATCH /memories/{id}`
- `DELETE /memories/{id}`

---

## Tasks

- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{id}`
- `PATCH /tasks/{id}`
- `DELETE /tasks/{id}`

---

## Files

- `POST /files` — multipart upload
- `GET /files`
- `GET /files/{id}`
- `DELETE /files/{id}`

---

## Settings

- `GET /settings`
- `PATCH /settings`

---

## Usage

- `GET /usage` — aggregated provider usage for the authenticated user

---

Detailed request/response schemas will be expanded as each endpoint is implemented.  
All endpoints enforce user isolation via JWT + RLS.
