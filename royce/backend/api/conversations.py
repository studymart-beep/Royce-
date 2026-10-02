"""Conversations API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.deps import CurrentUser
from database.supabase import get_service_client

router = APIRouter()


@router.get("")
async def list_conversations(user: CurrentUser, limit: int = 50):
    client = get_service_client()
    rows = (
        client.table("conversations")
        .select("id, title, model, provider, created_at, updated_at")
        .eq("user_id", user.user_id)
        .order("updated_at", desc=True)
        .limit(min(limit, 100))
        .execute()
    )
    return {"conversations": rows.data or []}


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, user: CurrentUser):
    client = get_service_client()
    conv = (
        client.table("conversations")
        .select("*")
        .eq("id", conversation_id)
        .eq("user_id", user.user_id)
        .maybe_single()
        .execute()
    )
    if not conv.data:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Conversation not found"}})
    msgs = (
        client.table("messages")
        .select("id, role, content, tool_calls, provider, model, created_at")
        .eq("conversation_id", conversation_id)
        .eq("user_id", user.user_id)
        .order("created_at")
        .limit(200)
        .execute()
    )
    return {**conv.data, "messages": msgs.data or []}


class PatchConversation(BaseModel):
    title: Optional[str] = None


@router.patch("/{conversation_id}")
async def patch_conversation(conversation_id: str, body: PatchConversation, user: CurrentUser):
    client = get_service_client()
    updates = {}
    if body.title is not None:
        updates["title"] = body.title
    if not updates:
        return {"ok": True}
    result = (
        client.table("conversations")
        .update(updates)
        .eq("id", conversation_id)
        .eq("user_id", user.user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Not found"}})
    return result.data[0]


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, user: CurrentUser):
    client = get_service_client()
    client.table("conversations").delete().eq("id", conversation_id).eq("user_id", user.user_id).execute()
    return {"ok": True}
