"""Mocked unit tests for AI providers and router. No real API keys required."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from ai.types import AIResponse, FinishReason, ProviderError, ProviderErrorType
from ai.providers.groq import GroqProvider
from ai.providers.cerebras import CerebrasProvider
from ai.providers.gemini import GeminiProvider
from ai.router import AIRouter
from ai.providers import build_provider_instances
from services.credentials import encrypt_api_key, decrypt_api_key, key_hint


# ---------------------------------------------------------------------------
# Credential crypto
# ---------------------------------------------------------------------------

def test_encrypt_decrypt_roundtrip(monkeypatch):
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("CREDENTIALS_ENCRYPTION_KEY", key)
    # Clear settings cache
    from config import get_settings
    get_settings.cache_clear()

    plain = "sk-test-secret-key-12345"
    cipher = encrypt_api_key(plain)
    assert cipher != plain
    assert decrypt_api_key(cipher) == plain
    assert key_hint(plain) == "••••2345"


def test_key_hint_short():
    assert key_hint("abc") == "••••"


# ---------------------------------------------------------------------------
# Groq provider
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_groq_success(httpx_mock):
    provider = GroqProvider()
    httpx_mock.add_response(
        url="https://api.groq.com/openai/v1/chat/completions",
        json={
            "id": "chatcmpl-1",
            "model": "llama-3.3-70b-versatile",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hello from Groq"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        },
    )
    resp = await provider.generate(
        [{"role": "user", "content": "Hi"}],
        api_key="gsk_test",
    )
    assert isinstance(resp, AIResponse)
    assert resp.content == "Hello from Groq"
    assert resp.provider == "groq"
    assert resp.finish_reason == FinishReason.STOP
    assert resp.usage.total_tokens == 15


@pytest.mark.asyncio
async def test_groq_auth_error(httpx_mock):
    provider = GroqProvider()
    httpx_mock.add_response(
        url="https://api.groq.com/openai/v1/chat/completions",
        status_code=401,
        json={"error": {"message": "Invalid API key"}},
    )
    with pytest.raises(ProviderError) as exc:
        await provider.generate(
            [{"role": "user", "content": "Hi"}],
            api_key="bad-key",
        )
    assert exc.value.error_type == ProviderErrorType.AUTH
    assert exc.value.retryable is False


@pytest.mark.asyncio
async def test_groq_rate_limit(httpx_mock):
    provider = GroqProvider()
    httpx_mock.add_response(
        url="https://api.groq.com/openai/v1/chat/completions",
        status_code=429,
        json={"error": {"message": "Rate limit"}},
    )
    with pytest.raises(ProviderError) as exc:
        await provider.generate(
            [{"role": "user", "content": "Hi"}],
            api_key="gsk_test",
        )
    assert exc.value.error_type == ProviderErrorType.RATE_LIMIT
    assert exc.value.retryable is True


@pytest.mark.asyncio
async def test_groq_missing_key():
    provider = GroqProvider()
    with pytest.raises(ProviderError) as exc:
        await provider.generate([{"role": "user", "content": "Hi"}], api_key="")
    assert exc.value.error_type == ProviderErrorType.AUTH


# ---------------------------------------------------------------------------
# Cerebras provider
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cerebras_success(httpx_mock):
    provider = CerebrasProvider()
    httpx_mock.add_response(
        url="https://api.cerebras.ai/v1/chat/completions",
        json={
            "id": "chatcmpl-c1",
            "model": "llama3.1-8b",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hello from Cerebras"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
        },
    )
    resp = await provider.generate(
        [{"role": "user", "content": "Hi"}],
        api_key="csk_test",
    )
    assert resp.content == "Hello from Cerebras"
    assert resp.provider == "cerebras"


@pytest.mark.asyncio
async def test_cerebras_invalid_request(httpx_mock):
    provider = CerebrasProvider()
    httpx_mock.add_response(
        url="https://api.cerebras.ai/v1/chat/completions",
        status_code=400,
        json={"error": {"message": "model not found"}},
    )
    with pytest.raises(ProviderError) as exc:
        await provider.generate(
            [{"role": "user", "content": "Hi"}],
            api_key="csk_test",
            model="nonexistent",
        )
    assert exc.value.error_type == ProviderErrorType.INVALID_REQUEST


# ---------------------------------------------------------------------------
# Router failover
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_router_failover_on_rate_limit():
    providers = build_provider_instances()

    async def fake_resolver(user_id: str) -> Dict[str, Dict[str, Any]]:
        return {
            "groq": {"api_key": "gsk_a", "is_enabled": True, "priority": 10, "preferred_model": None},
            "cerebras": {"api_key": "csk_b", "is_enabled": True, "priority": 20, "preferred_model": None},
        }

    router = AIRouter(providers, credential_resolver=fake_resolver)

    call_count = {"n": 0}

    async def groq_fail(*args, **kwargs):
        call_count["n"] += 1
        raise ProviderError("rate limited", error_type=ProviderErrorType.RATE_LIMIT, provider="groq", retryable=True)

    async def cerebras_ok(*args, **kwargs):
        call_count["n"] += 1
        return AIResponse(
            content="fallback works",
            provider="cerebras",
            model="llama3.1-8b",
            finish_reason=FinishReason.STOP,
        )

    with patch.object(providers["groq"], "generate", side_effect=groq_fail), \
         patch.object(providers["cerebras"], "generate", side_effect=cerebras_ok):
        resp = await router.generate(
            [{"role": "user", "content": "Hi"}],
            user_id="user-1",
            preferred_provider="groq",
        )

    assert resp.content == "fallback works"
    assert resp.provider == "cerebras"
    assert call_count["n"] == 2


@pytest.mark.asyncio
async def test_router_no_failover_on_auth_error():
    providers = build_provider_instances()

    async def fake_resolver(user_id: str) -> Dict[str, Dict[str, Any]]:
        return {
            "groq": {"api_key": "bad", "is_enabled": True, "priority": 10},
            "cerebras": {"api_key": "csk_b", "is_enabled": True, "priority": 20},
        }

    router = AIRouter(providers, credential_resolver=fake_resolver)

    async def groq_auth_fail(*args, **kwargs):
        raise ProviderError("bad key", error_type=ProviderErrorType.AUTH, provider="groq", retryable=False)

    with patch.object(providers["groq"], "generate", side_effect=groq_auth_fail):
        with pytest.raises(ProviderError) as exc:
            await router.generate(
                [{"role": "user", "content": "Hi"}],
                user_id="user-1",
                preferred_provider="groq",
            )
    assert exc.value.error_type == ProviderErrorType.AUTH


@pytest.mark.asyncio
async def test_router_no_credentials():
    providers = build_provider_instances()

    async def empty_resolver(user_id: str):
        return {}

    router = AIRouter(providers, credential_resolver=empty_resolver)
    with pytest.raises(ProviderError) as exc:
        await router.generate(
            [{"role": "user", "content": "Hi"}],
            user_id="user-1",
        )
    assert exc.value.error_type == ProviderErrorType.UNAVAILABLE
