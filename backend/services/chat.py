"""Chat orchestration service.

Authenticated user
  → load/create conversation
  → recent messages
  → relevant memories (placeholder until memory engine)
  → context builder
  → AI router
  → persist messages
  → record usage
  → return response
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ai.router import AIRouter
from ai.types import AIResponse
from database.supabase import get_service_client
from schemas.chat import ChatRequest, ChatResponse, TokenUsageSchema

logger = logging.getLogger("royce.chat")

RECENT_MESSAGE_LIMIT = 20
SYSTEM_PROMPT = (
    "You are Royce, a personal AI assistant. Be helpful, concise, and accurate. "
    "Use the provided context and memories when relevant."
)


class ChatService:
    def __init__(self, router: AIRouter):
        self.router = router

    async def chat(
        self,
        user_id: str,
        request: ChatRequest,
        request_id: Optional[str] = None,
    ) -> ChatResponse:
        client = get_service_client()

        # 1. Resolve conversation
        conversation_id = request.conversation_id
        if conversation_id:
            conv = (
                client.table("conversations")
                .select("id, user_id, title")
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .maybe_single()
                .execute()
            )
            if not conv.data:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail={
                    "error": {"code": "NOT_FOUND", "message": "Conversation not found"}
                })
        else:
            title = (request.message[:60] + "…") if len(request.message) > 60 else request.message
            created = (
                client.table("conversations")
                .insert({
                    "user_id": user_id,
                    "title": title,
                    "model": request.model,
                    "provider": request.provider,
                })
                .execute()
            )
            conversation_id = created.data[0]["id"]

        # 2. Load recent messages
        recent = (
            client.table("messages")
            .select("role, content, tool_calls")
            .eq("conversation_id", conversation_id)
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .limit(RECENT_MESSAGE_LIMIT)
            .execute()
        )
        history: List[Dict[str, Any]] = []
        for m in recent.data or []:
            entry: Dict[str, Any] = {"role": m["role"], "content": m.get("content") or ""}
            if m.get("tool_calls"):
                entry["tool_calls"] = m["tool_calls"]
            history.append(entry)

        # 3. Persist user message
        user_msg = (
            client.table("messages")
            .insert({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": "user",
                "content": request.message,
            })
            .execute()
        )

        # 4. Retrieve relevant long-term memories (user-scoped)
        memory_block = ""
        try:
            from memory.manager import MemoryManager
            mgr = MemoryManager()
            relevant = await mgr.search(user_id, request.message, limit=6)
            if relevant:
                lines = [f"- ({m.memory_type.value}) {m.content}" for m in relevant]
                memory_block = "Known about the user:\n" + "\n".join(lines)
        except Exception:
            logger.exception("Memory retrieval failed; continuing without memories")

        # Document RAG (separate from personal memory)
        doc_block = ""
        try:
            from services.files import search_file_chunks
            chunks = await search_file_chunks(user_id, request.message, limit=4)
            if chunks:
                lines = [f"- {c.get('content','')[:400]}" for c in chunks]
                doc_block = "Relevant document excerpts:\n" + "\n".join(lines)
        except Exception:
            logger.exception("Document retrieval failed")

        system_content = SYSTEM_PROMPT
        if memory_block:
            system_content = system_content + "\n\n" + memory_block
        if doc_block:
            system_content = system_content + "\n\n" + doc_block

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_content},
            *history,
            {"role": "user", "content": request.message},
        ]


        # 5. Call AI router (with tools) + tool execution loop
        from tools import registry as tool_registry

        tools = tool_registry.list_openai_tools()
        ai_response: AIResponse = await self.router.generate(
            messages,
            user_id=user_id,
            model=request.model,
            preferred_provider=request.provider,
            request_id=request_id,
            tools=tools if tools else None,
        )

        # Tool loop (max 3 rounds)
        for _round in range(3):
            if not ai_response.tool_calls:
                break
            for tc in ai_response.tool_calls:
                result = await tool_registry.execute(
                    tc.name, tc.arguments or {}, user_id=user_id
                )
                messages.append(
                    {
                        "role": "assistant",
                        "content": ai_response.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": __import__("json").dumps(tc.arguments or {}),
                                },
                            }
                        ],
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": __import__("json").dumps(result),
                    }
                )
            ai_response = await self.router.generate(
                messages,
                user_id=user_id,
                model=request.model,
                preferred_provider=request.provider,
                request_id=request_id,
                tools=tools if tools else None,
            )

        # Optional memory extraction (candidates only logged for V1 auto-save of strong signals)
        try:
            from memory.manager import MemoryManager
            candidates = MemoryManager().extract_candidates(request.message, ai_response.content)
            for c in candidates[:2]:
                await MemoryManager().create(
                    user_id,
                    __import__("memory.types", fromlist=["MemoryCreate"]).MemoryCreate(
                        content=c, memory_type=__import__("memory.types", fromlist=["MemoryType"]).MemoryType.FACT
                    ),
                )
        except Exception:
            logger.exception("Memory extraction skipped")

        # 6. Persist assistant message
        tool_calls_payload = [
            {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
            for tc in (ai_response.tool_calls or [])
        ]
        usage_payload = None
        if ai_response.usage:
            usage_payload = {
                "input_tokens": ai_response.usage.input_tokens,
                "output_tokens": ai_response.usage.output_tokens,
                "total_tokens": ai_response.usage.total_tokens,
            }

        asst_msg = (
            client.table("messages")
            .insert({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": "assistant",
                "content": ai_response.content,
                "tool_calls": tool_calls_payload or None,
                "provider": ai_response.provider,
                "model": ai_response.model,
                "token_usage": usage_payload,
                "metadata": ai_response.metadata or {},
            })
            .execute()
        )
        message_id = asst_msg.data[0]["id"]

        # 7. Update conversation timestamp + last provider/model
        client.table("conversations").update({
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": ai_response.provider,
            "model": ai_response.model,
        }).eq("id", conversation_id).eq("user_id", user_id).execute()

        # 8. Record usage
        try:
            client.table("provider_usage").insert({
                "user_id": user_id,
                "request_id": (ai_response.metadata or {}).get("request_id") or request_id,
                "provider": ai_response.provider,
                "model": ai_response.model,
                "success": True,
                "latency_ms": (ai_response.metadata or {}).get("latency_ms"),
                "input_tokens": ai_response.usage.input_tokens if ai_response.usage else None,
                "output_tokens": ai_response.usage.output_tokens if ai_response.usage else None,
                "total_tokens": ai_response.usage.total_tokens if ai_response.usage else None,
            }).execute()
        except Exception:
            logger.exception("Failed to record provider usage")

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            role="assistant",
            content=ai_response.content,
            provider=ai_response.provider,
            model=ai_response.model,
            tool_calls=tool_calls_payload,
            usage=TokenUsageSchema(**usage_payload) if usage_payload else None,
        )
