"""Memory tool — search or save user memories."""

from __future__ import annotations

from typing import Any, Dict

from memory.manager import MemoryManager
from memory.types import MemoryCreate, MemoryType
from tools.registry import ToolDefinition, registry


async def memory_handler(args: Dict[str, Any], *, user_id: str) -> Dict[str, Any]:
    action = str(args.get("action", "search")).lower()
    mgr = MemoryManager()
    if action == "search":
        query = str(args.get("query", "")).strip()
        if not query:
            return {"error": "query required"}
        results = await mgr.search(user_id, query, limit=5)
        return {
            "memories": [
                {"id": m.id, "content": m.content, "type": m.memory_type.value, "similarity": m.similarity}
                for m in results
            ]
        }
    if action == "save":
        content = str(args.get("content", "")).strip()
        if not content:
            return {"error": "content required"}
        mtype = args.get("memory_type") or "fact"
        try:
            mt = MemoryType(mtype)
        except Exception:
            mt = MemoryType.FACT
        rec = await mgr.create(user_id, MemoryCreate(content=content, memory_type=mt))
        return {"memory": {"id": rec.id, "content": rec.content}}
    return {"error": f"Unknown action: {action}"}


registry.register(
    ToolDefinition(
        name="memory",
        description="Search or save long-term memories about the user. Actions: search, save.",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["search", "save"]},
                "query": {"type": "string"},
                "content": {"type": "string"},
                "memory_type": {
                    "type": "string",
                    "enum": ["preference", "fact", "project", "goal", "instruction", "recurring", "other"],
                },
            },
            "required": ["action"],
        },
    ),
    memory_handler,
)
