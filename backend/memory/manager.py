"""Memory manager: create, list, update, delete, extract candidates."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from database.supabase import get_service_client
from memory.embeddings import embed_text
from memory.retrieval import search_memories
from memory.types import MemoryCreate, MemoryRecord, MemoryType

logger = logging.getLogger("royce.memory.manager")

# Simple V1 heuristics for durable facts (not every message)
_DURABLE_PATTERNS = [
    re.compile(r"\b(my name is|i am|i'm|i live|i work|i prefer|i like|i hate|always|never)\b", re.I),
    re.compile(r"\b(remember that|don't forget|note that)\b", re.I),
]


class MemoryManager:
    async def create(self, user_id: str, data: MemoryCreate, *, embedding_api_key: Optional[str] = None) -> MemoryRecord:
        vector = await embed_text(data.content, api_key=embedding_api_key)
        client = get_service_client()
        payload = {
            "user_id": user_id,
            "content": data.content.strip(),
            "embedding": vector,
            "memory_type": data.memory_type.value,
            "importance": data.importance,
            "source_message_id": data.source_message_id,
            "metadata": data.metadata or {},
        }
        result = client.table("memories").insert(payload).execute()
        row = result.data[0]
        return MemoryRecord(
            id=row["id"],
            user_id=row["user_id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            importance=row["importance"],
            source_message_id=row.get("source_message_id"),
            metadata=row.get("metadata") or {},
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    async def list_for_user(self, user_id: str, limit: int = 50) -> List[MemoryRecord]:
        client = get_service_client()
        result = (
            client.table("memories")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [
            MemoryRecord(
                id=r["id"],
                user_id=r["user_id"],
                content=r["content"],
                memory_type=MemoryType(r.get("memory_type") or "fact"),
                importance=float(r.get("importance") or 0.5),
                metadata=r.get("metadata") or {},
                created_at=r.get("created_at"),
                updated_at=r.get("updated_at"),
            )
            for r in (result.data or [])
            if r.get("user_id") == user_id
        ]

    async def delete(self, user_id: str, memory_id: str) -> bool:
        client = get_service_client()
        client.table("memories").delete().eq("id", memory_id).eq("user_id", user_id).execute()
        return True

    async def search(self, user_id: str, query: str, limit: int = 8) -> List[MemoryRecord]:
        return await search_memories(user_id, query, limit=limit)

    def extract_candidates(self, user_message: str, assistant_message: Optional[str] = None) -> List[str]:
        """
        V1 heuristic extraction — does NOT auto-save every message.
        Returns candidate strings for optional persistence.
        """
        candidates: List[str] = []
        text = user_message.strip()
        if len(text) < 12:
            return candidates
        for pat in _DURABLE_PATTERNS:
            if pat.search(text):
                # Keep short, self-contained sentences
                for sent in re.split(r"[.!?\n]+", text):
                    s = sent.strip()
                    if 12 <= len(s) <= 300 and pat.search(s):
                        candidates.append(s)
                break
        # de-dupe
        seen = set()
        unique = []
        for c in candidates:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique[:5]
