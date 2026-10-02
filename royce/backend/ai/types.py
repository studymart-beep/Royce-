"""Normalized AI types used across the entire Royce backend."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FinishReason(str, Enum):
    STOP = "stop"
    TOOL_CALLS = "tool_calls"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    UNKNOWN = "unknown"


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class TokenUsage(BaseModel):
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class AIResponse(BaseModel):
    """Normalized response returned by every provider implementation."""

    content: Optional[str] = None
    provider: str
    model: str
    finish_reason: FinishReason = FinishReason.STOP
    tool_calls: List[ToolCall] = Field(default_factory=list)
    usage: Optional[TokenUsage] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw: Optional[Any] = None  # original provider payload for debugging (never sent to client)


class ProviderErrorType(str, Enum):
    AUTH = "auth"
    INVALID_REQUEST = "invalid_request"
    RATE_LIMIT = "rate_limit"
    TRANSIENT = "transient"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ProviderError(Exception):
    """Raised by providers; classified so the router can decide on failover."""

    def __init__(
        self,
        message: str,
        *,
        error_type: ProviderErrorType = ProviderErrorType.UNKNOWN,
        provider: str = "",
        status_code: Optional[int] = None,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}
