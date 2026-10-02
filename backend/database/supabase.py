"""Supabase client helpers.

- Anon client: for operations that respect RLS (when a user JWT is attached)
- Service client: privileged operations after identity has been verified
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from config import get_settings


@lru_cache
def get_service_client():
    """Service-role client. NEVER expose this to the browser."""
    from supabase import create_client

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_user_client(access_token: str):
    """
    Client scoped to a user JWT so RLS policies apply.
    Useful for direct user-scoped queries when preferred.
    """
    from supabase import create_client

    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client
