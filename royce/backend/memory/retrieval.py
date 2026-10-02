"""Semantic memory retrieval via pgvector (user-scoped)."""

from __future__ import annotations

import logging
from typing import List, Optional

from database.supabase import get_service_client
from memory.embeddings import embed_text
from memory.types import MemoryRecord, MemoryType

logger = logging.getLogger("royce.memory.retrieval")


async def search_memories(
    user_id: str,
    query: str,
    *,
    limit: int = 8,
    min_similarity: float = 0.25,
    memory_types: Optional[List[str]] = None,
    embedding_api_key: Optional[str] = None,
) -> List[MemoryRecord]:
    """
    Always scoped to user_id. Never crosses user boundaries.
    Uses cosine distance via pgvector when embeddings exist.
    """
    if not query.strip() or not user_id:
        return []

    vector = await embed_text(query, api_key=embedding_api_key)
    client = get_service_client()

    # RPC preferred; fall back to client-side filter if function missing
    try:
        result = client.rpc(
            "match_memories",
            {
                "query_embedding": vector,
                "match_user_id": user_id,
                "match_count": limit,
                "match_threshold": min_similarity,
            },
        ).execute()
        rows = result.data or []
    except Exception as e:
        logger.warning("match_memories RPC unavailable (%s); using basic fetch", e)
        # Fallback: fetch recent memories for user (no vector rank)
        q = (
            client.table("memories")
            .select("*")
            .eq("user_id", user_id)
            .order("importance", desc=True)
            .limit(limit)
        )
        if memory_types:
            q = q.in_("memory_type", memory_types)
        rows = (q.execute().data) or []

    memories: List[MemoryRecord] = []
    for row in rows:
        if row.get("user_id") != user_id:
            continue  # defense in depth
        sim = row.get("similarity")
        memories.append(
            MemoryRecord(
                id=row["id"],
                user_id=row["user_id"],
                content=row["content"],
                memory_type=MemoryType(row.get("memory_type") or "fact"),
                importance=float(row.get("importance") or 0.5),
                source_message_id=row.get("source_message_id"),
                metadata=row.get("metadata") or {},
                confidence=float(row.get("confidence") or 1.0),
                similarity=float(sim) if sim is not None else None,
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            )
        )
    return memories
