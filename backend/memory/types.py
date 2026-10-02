"""Memory domain types."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    PROJECT = "project"
    GOAL = "goal"
    INSTRUCTION = "instruction"
    RECURRING = "recurring"
    OTHER = "other"


class MemoryRecord(BaseModel):
    id: str
    user_id: str
    content: str
    memory_type: MemoryType = MemoryType.FACT
    importance: float = 0.5
    source_message_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    similarity: Optional[float] = None  # filled on retrieval
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    memory_type: MemoryType = MemoryType.FACT
    importance: float = Field(0.5, ge=0, le=1)
    source_message_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySearchResult(BaseModel):
    memories: List[MemoryRecord]
    query: str
