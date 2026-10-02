"""AI Router — selects provider, supplies per-user credentials, handles failover, records usage."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from ai.providers.base import BaseProvider
from ai.types import AIResponse, ProviderError, ProviderErrorType
from config import get_settings

logger = logging.getLogger("royce.ai.router")


class AIRouter:
    """
    providers: registry of name -> BaseProvider instance (stateless; keys come per-call)
    credential_resolver: async callable(user_id) -> Dict[provider_name, {api_key, preferred_model, priority, is_enabled}]
    """

    def __init__(
        self,
        providers: Dict[str, BaseProvider],
        credential_resolver: Optional[Any] = None,
    ):
        self.providers = providers
        self.credential_resolver = credential_resolver
        self.settings = get_settings()

    async def _load_user_credentials(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        if not self.credential_resolver:
            return {}
        return await self.credential_resolver(user_id)

    def _select_order(
        self,
        available: Dict[str, Dict[str, Any]],
        preferred: Optional[str] = None,
    ) -> List[str]:
        """
        Deterministic order:
        1. Explicit preferred (if enabled + has key)
        2. User-configured priority (lower number first)
        3. Global default / fallback list
        """
        enabled = {
            name: meta
            for name, meta in available.items()
            if meta.get("is_enabled", True) and meta.get("api_key") and name in self.providers
        }

        order: List[str] = []
        if preferred and preferred in enabled:
            order.append(preferred)

        # Sort remaining by priority ascending
        remaining = sorted(
            [(n, m.get("priority", 100)) for n, m in enabled.items() if n not in order],
            key=lambda x: x[1],
        )
        for name, _ in remaining:
            order.append(name)

        # If nothing user-configured, fall back to global defaults (still need keys)
        if not order:
            for name in [self.settings.ai_default_provider] + self.settings.fallback_provider_list:
                if name in enabled and name not in order:
                    order.append(name)

        return order

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        *,
        user_id: str,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        preferred_provider: Optional[str] = None,
        request_id: Optional[str] = None,
        timeout: float = 45.0,
        temperature: float = 0.55,
        max_tokens: Optional[int] = 1024,
        **kwargs: Any,
    ) -> AIResponse:
        if not user_id:
            raise ProviderError(
                "user_id is required to resolve provider credentials",
                error_type=ProviderErrorType.AUTH,
            )

        creds = await self._load_user_credentials(user_id)
        order = self._select_order(creds, preferred_provider)

        if not order:
            raise ProviderError(
                "No enabled AI providers with valid credentials for this user. "
                "Add an API key in Settings → Providers.",
                error_type=ProviderErrorType.UNAVAILABLE,
            )

        last_error: Optional[ProviderError] = None
        request_id = request_id or str(uuid.uuid4())

        for name in order:
            provider = self.providers[name]
            meta = creds[name]
            api_key = meta["api_key"]
            # Prefer request model → user preferred_model → provider default
            effective_model = model or meta.get("preferred_model") or provider.default_model

            start = time.perf_counter()
            try:
                logger.info(
                    "Attempting provider=%s model=%s request_id=%s user_id=%s",
                    name,
                    effective_model,
                    request_id,
                    user_id,
                )
                response = await provider.generate(
                    messages,
                    api_key=api_key,
                    model=effective_model,
                    tools=tools,
                    timeout=timeout,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                latency_ms = int((time.perf_counter() - start) * 1000)
                logger.info(
                    "Success provider=%s model=%s latency_ms=%s request_id=%s",
                    response.provider,
                    response.model,
                    latency_ms,
                    request_id,
                )
                # Attach latency for upstream usage recording
                response.metadata = response.metadata or {}
                response.metadata["latency_ms"] = latency_ms
                response.metadata["request_id"] = request_id
                return response
            except ProviderError as e:
                latency_ms = int((time.perf_counter() - start) * 1000)
                logger.warning(
                    "Provider error provider=%s type=%s latency_ms=%s request_id=%s msg=%s",
                    name,
                    e.error_type,
                    latency_ms,
                    request_id,
                    str(e),
                )
                last_error = e
                # Do not failover on auth or invalid request
                if e.error_type in (
                    ProviderErrorType.AUTH,
                    ProviderErrorType.INVALID_REQUEST,
                ):
                    raise
                continue
            except Exception as e:
                latency_ms = int((time.perf_counter() - start) * 1000)
                logger.exception(
                    "Unexpected provider failure provider=%s request_id=%s",
                    name,
                    request_id,
                )
                last_error = ProviderError(
                    str(e),
                    error_type=ProviderErrorType.UNKNOWN,
                    provider=name,
                    retryable=True,
                )
                continue

        raise last_error or ProviderError(
            "All providers failed",
            error_type=ProviderErrorType.UNAVAILABLE,
        )
