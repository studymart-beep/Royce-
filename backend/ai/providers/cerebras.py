"""Cerebras Cloud provider (OpenAI-compatible API)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from ai.providers.base import BaseProvider
from ai.types import (
    AIResponse,
    FinishReason,
    ProviderError,
    ProviderErrorType,
    TokenUsage,
    ToolCall,
)

logger = logging.getLogger("royce.ai.cerebras")

CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
DEFAULT_MODEL = "llama3.1-8b"


class CerebrasProvider(BaseProvider):
    name = "cerebras"
    default_model = DEFAULT_MODEL

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        *,
        api_key: str,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 45.0,
        **kwargs: Any,
    ) -> AIResponse:
        if not api_key or not api_key.strip():
            raise ProviderError(
                "Cerebras API key is missing",
                error_type=ProviderErrorType.AUTH,
                provider=self.name,
            )

        model_id = model or self.default_model
        payload: Dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{CEREBRAS_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
            return self._parse_response(resp, model_id)
        except httpx.TimeoutException as e:
            raise ProviderError(
                f"Cerebras request timed out after {timeout}s",
                error_type=ProviderErrorType.TIMEOUT,
                provider=self.name,
                retryable=True,
            ) from e
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(
                str(e),
                error_type=ProviderErrorType.UNKNOWN,
                provider=self.name,
                retryable=True,
            ) from e

    def _parse_response(self, resp: httpx.Response, model_id: str) -> AIResponse:
        if resp.status_code in (401, 403):
            raise ProviderError(
                "Cerebras authentication failed",
                error_type=ProviderErrorType.AUTH,
                provider=self.name,
                status_code=resp.status_code,
                retryable=False,
            )
        if resp.status_code == 429:
            raise ProviderError(
                "Cerebras rate limit exceeded",
                error_type=ProviderErrorType.RATE_LIMIT,
                provider=self.name,
                status_code=429,
                retryable=True,
            )
        if resp.status_code == 400:
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                detail = resp.text
            raise ProviderError(
                f"Cerebras invalid request: {detail}",
                error_type=ProviderErrorType.INVALID_REQUEST,
                provider=self.name,
                status_code=400,
                retryable=False,
            )
        if resp.status_code >= 500:
            raise ProviderError(
                f"Cerebras server error ({resp.status_code})",
                error_type=ProviderErrorType.TRANSIENT,
                provider=self.name,
                status_code=resp.status_code,
                retryable=True,
            )
        if resp.status_code != 200:
            raise ProviderError(
                f"Cerebras unexpected status {resp.status_code}: {resp.text[:200]}",
                error_type=ProviderErrorType.UNKNOWN,
                provider=self.name,
                status_code=resp.status_code,
                retryable=True,
            )

        data = resp.json()
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content")
        finish_raw = choice.get("finish_reason") or "stop"
        finish_map = {
            "stop": FinishReason.STOP,
            "tool_calls": FinishReason.TOOL_CALLS,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
        }
        finish = finish_map.get(finish_raw, FinishReason.UNKNOWN)

        tool_calls: List[ToolCall] = []
        for tc in message.get("tool_calls") or []:
            fn = tc.get("function") or {}
            args_raw = fn.get("arguments") or "{}"
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except Exception:
                args = {}
            tool_calls.append(
                ToolCall(
                    id=tc.get("id") or f"call_{fn.get('name')}",
                    name=fn.get("name") or "",
                    arguments=args if isinstance(args, dict) else {},
                )
            )

        usage_data = data.get("usage") or {}
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens"),
            output_tokens=usage_data.get("completion_tokens"),
            total_tokens=usage_data.get("total_tokens"),
        )

        return AIResponse(
            content=content,
            provider=self.name,
            model=data.get("model") or model_id,
            finish_reason=finish,
            tool_calls=tool_calls,
            usage=usage,
            metadata={"id": data.get("id")},
        )
