"""Files tool — list user's files metadata."""

from __future__ import annotations

from typing import Any, Dict

from database.supabase import get_service_client
from tools.registry import ToolDefinition, registry


async def files_handler(args: Dict[str, Any], *, user_id: str) -> Dict[str, Any]:
    client = get_service_client()
    rows = (
        client.table("files")
        .select("id, filename, mime_type, size_bytes, status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    return {"files": rows.data or []}


registry.register(
    ToolDefinition(
        name="files",
        description="List the user's uploaded files (metadata only).",
        parameters={"type": "object", "properties": {}},
    ),
    files_handler,
)
