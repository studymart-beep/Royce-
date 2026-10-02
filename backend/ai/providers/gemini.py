"""Google Gemini provider (google-genai SDK)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai.providers.base import BaseProvider
from ai.types import (
    AIResponse,
    FinishReason,
    ProviderError,
    ProviderErrorType,
    TokenUsage,
    ToolCall,
)

logger = logging.getLogger("royce.ai.gemini")

# Stable default; can be overridden per-user or per-request
DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiProvider(BaseProvider):
    name = "gemini"
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
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> AIResponse:
        if not api_key or not api_key.strip():
            raise ProviderError(
                "Gemini API key is missing",
                error_type=ProviderErrorType.AUTH,
                provider=self.name,
            )

        model_id = model or self.default_model

        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError as e:
            raise ProviderError(
                "google-genai package is not installed",
                error_type=ProviderErrorType.UNAVAILABLE,
                provider=self.name,
            ) from e

        try:
            client = genai.Client(api_key=api_key)

            # Convert OpenAI-style messages → Gemini contents
            system_instruction = None
            contents: List[Any] = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content") or ""
                if role == "system":
                    system_instruction = content if system_instruction is None else f"{system_instruction}\n{content}"
                    continue
                gemini_role = "model" if role == "assistant" else "user"
                contents.append(
                    genai_types.Content(
                        role=gemini_role,
                        parts=[genai_types.Part.from_text(text=str(content))],
                    )
                )

            config_kwargs: Dict[str, Any] = {
                "temperature": temperature,
            }
            if max_tokens is not None:
                config_kwargs["max_output_tokens"] = max_tokens
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            # Basic tool support (function declarations) if provided
            if tools:
                function_decls = []
                for t in tools:
                    fn = t.get("function") or t
                    function_decls.append(
                        genai_types.FunctionDeclaration(
                            name=fn.get("name", ""),
                            description=fn.get("description", ""),
                            parameters=fn.get("parameters") or {},
                        )
                    )
                if function_decls:
                    config_kwargs["tools"] = [
                        genai_types.Tool(function_declarations=function_decls)
                    ]

            config = genai_types.GenerateContentConfig(**config_kwargs)

            response = client.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )

            text = getattr(response, "text", None) or ""
            finish = FinishReason.STOP
            tool_calls: List[ToolCall] = []

            # Extract function calls if present
            try:
                candidates = getattr(response, "candidates", None) or []
                if candidates:
                    parts = getattr(candidates[0].content, "parts", None) or []
                    for part in parts:
                        fc = getattr(part, "function_call", None)
                        if fc:
                            finish = FinishReason.TOOL_CALLS
                            args = dict(fc.args) if hasattr(fc, "args") and fc.args else {}
                            tool_calls.append(
                                ToolCall(
                                    id=f"call_{fc.name}",
                                    name=fc.name,
                                    arguments=args,
                                )
                            )
            except Exception:
                pass

            usage = None
            try:
                meta = getattr(response, "usage_metadata", None)
                if meta:
                    usage = TokenUsage(
                        input_tokens=getattr(meta, "prompt_token_count", None),
                        output_tokens=getattr(meta, "candidates_token_count", None),
                        total_tokens=getattr(meta, "total_token_count", None),
                    )
            except Exception:
                pass

            return AIResponse(
                content=text if not tool_calls else (text or None),
                provider=self.name,
                model=model_id,
                finish_reason=finish,
                tool_calls=tool_calls,
                usage=usage,
                metadata={},
            )

        except ProviderError:
            raise
        except Exception as e:
            raise self._classify(e) from e

    def _classify(self, exc: Exception) -> ProviderError:
        msg = str(exc).lower()
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)

        if any(x in msg for x in ("api key", "api_key", "unauthorized", "401", "permission denied", "invalid api key")):
            return ProviderError(
                str(exc),
                error_type=ProviderErrorType.AUTH,
                provider=self.name,
                status_code=401,
                retryable=False,
            )
        if any(x in msg for x in ("rate limit", "429", "quota", "resource exhausted")):
            return ProviderError(
                str(exc),
                error_type=ProviderErrorType.RATE_LIMIT,
                provider=self.name,
                status_code=429,
                retryable=True,
            )
        if any(x in msg for x in ("timeout", "timed out", "deadline")):
            return ProviderError(
                str(exc),
                error_type=ProviderErrorType.TIMEOUT,
                provider=self.name,
                retryable=True,
            )
        if any(x in msg for x in ("invalid", "400", "bad request", "malformed")):
            return ProviderError(
                str(exc),
                error_type=ProviderErrorType.INVALID_REQUEST,
                provider=self.name,
                status_code=400,
                retryable=False,
            )
        if any(x in msg for x in ("503", "unavailable", "overloaded", "500", "502", "504")):
            return ProviderError(
                str(exc),
                error_type=ProviderErrorType.TRANSIENT,
                provider=self.name,
                retryable=True,
            )
        return ProviderError(
            str(exc),
            error_type=ProviderErrorType.UNKNOWN,
            provider=self.name,
            status_code=status if isinstance(status, int) else None,
            retryable=True,
        )
