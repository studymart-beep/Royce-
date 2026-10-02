"""Tasks tool — list/create tasks for the authenticated user."""

from __future__ import annotations

from typing import Any, Dict

from database.supabase import get_service_client
from tools.registry import ToolDefinition, registry


async def tasks_handler(args: Dict[str, Any], *, user_id: str) -> Dict[str, Any]:
    action = str(args.get("action", "list")).lower()
    client = get_service_client()
    if action == "list":
        status = args.get("status")
        q = client.table("tasks").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(20)
        if status:
            q = q.eq("status", status)
        rows = (q.execute().data) or []
        return {"tasks": rows}
    if action == "create":
        title = str(args.get("title", "")).strip()
        if not title:
            return {"error": "title required"}
        row = (
            client.table("tasks")
            .insert(
                {
                    "user_id": user_id,
                    "title": title,
                    "description": args.get("description"),
                    "status": "todo",
                    "due_at": args.get("due_at"),
                }
            )
            .execute()
        )
        return {"task": (row.data or [None])[0]}
    if action == "complete":
        task_id = args.get("task_id")
        if not task_id:
            return {"error": "task_id required"}
        row = (
            client.table("tasks")
            .update({"status": "done"})
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )
        return {"task": (row.data or [None])[0]}
    return {"error": f"Unknown action: {action}"}


registry.register(
    ToolDefinition(
        name="tasks",
        description="List, create, or complete the user's tasks. Actions: list, create, complete.",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "complete"]},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "due_at": {"type": "string", "description": "ISO datetime"},
                "task_id": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "done", "cancelled"]},
            },
            "required": ["action"],
        },
    ),
    tasks_handler,
)
