"""Chat request/response schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=100_000)
    model: Optional[str] = None
    provider: Optional[str] = None
    stream: bool = False


class TokenUsageSchema(BaseModel):
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: Optional[str] = None
    provider: str
    model: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Optional[TokenUsageSchema] = None


class ConversationSummary(BaseModel):
    id: str
    title: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    created_at: str
    updated_at: str


class MessageSchema(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    created_at: str


class ConversationDetail(BaseModel):
    id: str
    title: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    created_at: str
    updated_at: str
    messages: List[MessageSchema] = Field(default_factory=list)
