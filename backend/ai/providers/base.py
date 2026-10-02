"""Abstract base class for all AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ai.types import AIResponse


class BaseProvider(ABC):
    """
    Every concrete provider must implement this interface.
    Credentials are supplied per-call (from the authenticated user's encrypted store),
    never from process environment variables.
    """

    name: str = "base"
    default_model: str = ""

    def __init__(self, **kwargs: Any):
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        *,
        api_key: str,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> AIResponse:
        """
        Generate a completion using the caller-supplied API key.

        messages: list of {"role": "...", "content": "..."} (and optional tool fields)
        api_key: decrypted provider key for the current user (never logged)
        tools: OpenAI-style tool definitions where supported
        """
        ...

    async def health_check(self, api_key: str) -> bool:
        """Lightweight probe; subclasses may override."""
        return bool(api_key and api_key.strip())
