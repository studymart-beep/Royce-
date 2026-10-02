"""Tool registry — name, description, schema, execute."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("royce.tools")

ToolFn = Callable[..., Awaitable[Dict[str, Any]]]


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    requires_user: bool = True


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, ToolFn] = {}

    def register(self, definition: ToolDefinition, handler: ToolFn) -> None:
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    def list_openai_tools(self) -> List[Dict[str, Any]]:
        """OpenAI-compatible tool definitions for providers that support them."""
        out = []
        for t in self._tools.values():
            out.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
            )
        return out

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    async def execute(
        self,
        name: str,
        arguments: Dict[str, Any],
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        if name not in self._handlers:
            return {"error": f"Unknown tool: {name}"}
        try:
            return await self._handlers[name](arguments, user_id=user_id)
        except Exception as e:
            logger.exception("Tool %s failed", name)
            return {"error": str(e)}


# Singleton populated at import of tool modules
registry = ToolRegistry()
