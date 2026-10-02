"""Memories API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from api.deps import CurrentUser
from memory.manager import MemoryManager
from memory.types import MemoryCreate, MemoryType

router = APIRouter()
mgr = MemoryManager()


class MemoryBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    memory_type: str = "fact"
    importance: float = 0.5


@router.get("")
async def list_memories(user: CurrentUser, q: Optional[str] = None):
    if q:
        results = await mgr.search(user.user_id, q, limit=20)
        return {
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "memory_type": m.memory_type.value,
                    "importance": m.importance,
                    "similarity": m.similarity,
                    "created_at": m.created_at,
                }
                for m in results
            ]
        }
    rows = await mgr.list_for_user(user.user_id)
    return {
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "memory_type": m.memory_type.value,
                "importance": m.importance,
                "created_at": m.created_at,
            }
            for m in rows
        ]
    }


@router.post("")
async def create_memory(body: MemoryBody, user: CurrentUser):
    try:
        mt = MemoryType(body.memory_type)
    except Exception:
        mt = MemoryType.FACT
    rec = await mgr.create(
        user.user_id,
        MemoryCreate(content=body.content, memory_type=mt, importance=body.importance),
    )
    return {
        "id": rec.id,
        "content": rec.content,
        "memory_type": rec.memory_type.value,
        "importance": rec.importance,
        "created_at": rec.created_at,
    }


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, user: CurrentUser):
    await mgr.delete(user.user_id, memory_id)
    return {"ok": True}
