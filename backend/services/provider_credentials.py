"""Load and manage per-user AI provider credentials."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from database.supabase import get_service_client
from services.credentials import (
    decrypt_api_key,
    encrypt_api_key,
    key_hint,
    public_credential_view,
    CredentialCryptoError,
)

logger = logging.getLogger("royce.provider_credentials")


async def resolve_credentials_for_user(user_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Return {provider: {api_key, preferred_model, priority, is_enabled}} for the router.
    Decrypts keys server-side. Never expose this dict to the client.
    """
    client = get_service_client()
    result = (
        client.table("provider_credentials")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_enabled", True)
        .execute()
    )
    out: Dict[str, Dict[str, Any]] = {}
    for row in result.data or []:
        try:
            plain = decrypt_api_key(row["encrypted_api_key"])
        except CredentialCryptoError:
            logger.error("Failed to decrypt credential for user=%s provider=%s", user_id, row.get("provider"))
            continue
        out[row["provider"]] = {
            "api_key": plain,
            "preferred_model": row.get("preferred_model"),
            "priority": row.get("priority", 100),
            "is_enabled": row.get("is_enabled", True),
        }
    return out


async def list_credentials(user_id: str) -> List[Dict[str, Any]]:
    """Public view (no raw keys)."""
    client = get_service_client()
    result = (
        client.table("provider_credentials")
        .select("*")
        .eq("user_id", user_id)
        .order("priority")
        .execute()
    )
    return [public_credential_view(r) for r in (result.data or [])]


async def upsert_credential(
    user_id: str,
    provider: str,
    api_key: str,
    *,
    preferred_model: Optional[str] = None,
    priority: int = 100,
    is_enabled: bool = True,
) -> Dict[str, Any]:
    client = get_service_client()
    encrypted = encrypt_api_key(api_key)
    hint = key_hint(api_key)
    payload = {
        "user_id": user_id,
        "provider": provider,
        "encrypted_api_key": encrypted,
        "key_hint": hint,
        "preferred_model": preferred_model,
        "priority": priority,
        "is_enabled": is_enabled,
        "updated_at": "now()",
    }
    result = (
        client.table("provider_credentials")
        .upsert(payload, on_conflict="user_id,provider")
        .execute()
    )
    row = (result.data or [payload])[0]
    return public_credential_view(row)


async def delete_credential(user_id: str, provider: str) -> bool:
    client = get_service_client()
    result = (
        client.table("provider_credentials")
        .delete()
        .eq("user_id", user_id)
        .eq("provider", provider)
        .execute()
    )
    return True


async def update_credential_meta(
    user_id: str,
    provider: str,
    *,
    preferred_model: Optional[str] = None,
    priority: Optional[int] = None,
    is_enabled: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    client = get_service_client()
    updates: Dict[str, Any] = {"updated_at": "now()"}
    if preferred_model is not None:
        updates["preferred_model"] = preferred_model
    if priority is not None:
        updates["priority"] = priority
    if is_enabled is not None:
        updates["is_enabled"] = is_enabled
    result = (
        client.table("provider_credentials")
        .update(updates)
        .eq("user_id", user_id)
        .eq("provider", provider)
        .execute()
    )
    if not result.data:
        return None
    return public_credential_view(result.data[0])
