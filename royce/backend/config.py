"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


class Settings:
    def __init__(self) -> None:
        # Load .env file if present
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.isfile(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v

        self.supabase_url = _env("SUPABASE_URL")
        self.supabase_anon_key = _env("SUPABASE_ANON_KEY")
        self.supabase_service_role_key = _env("SUPABASE_SERVICE_ROLE_KEY")
        self.credentials_encryption_key = _env("CREDENTIALS_ENCRYPTION_KEY")
        self.ai_default_provider = _env("AI_DEFAULT_PROVIDER", "gemini")
        self.ai_fallback_providers = _env("AI_FALLBACK_PROVIDERS", "groq,cerebras")
        self.web_search_api_key = _env("WEB_SEARCH_API_KEY") or None
        self.web_search_provider = _env("WEB_SEARCH_PROVIDER", "tavily")
        self.environment = _env("ENVIRONMENT", "development")
        self.log_level = _env("LOG_LEVEL", "INFO")
        self.cors_origins = _env("CORS_ORIGINS", "http://localhost:3000")
        self.max_upload_size_mb = int(_env("MAX_UPLOAD_SIZE_MB", "20") or "20")
        self.request_timeout_seconds = int(_env("REQUEST_TIMEOUT_SECONDS", "60") or "60")
        self.backend_url = _env("BACKEND_URL", "http://localhost:8000")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def fallback_provider_list(self) -> List[str]:
        return [p.strip() for p in self.ai_fallback_providers.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
