"""Secure storage and retrieval of per-user AI provider API keys.

Keys are encrypted with Fernet (symmetric) using CREDENTIALS_ENCRYPTION_KEY.
The raw key is never returned to the client after storage; only a hint (last 4 chars)
is exposed for UI display.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken

from config import get_settings

logger = logging.getLogger("royce.credentials")


class CredentialCryptoError(Exception):
    pass


def _fernet() -> Fernet:
    settings = get_settings()
    key = settings.credentials_encryption_key
    if not key:
        raise CredentialCryptoError(
            "CREDENTIALS_ENCRYPTION_KEY is not configured. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        raise CredentialCryptoError(f"Invalid CREDENTIALS_ENCRYPTION_KEY: {e}") from e


def encrypt_api_key(plain_key: str) -> str:
    if not plain_key or not plain_key.strip():
        raise ValueError("API key cannot be empty")
    return _fernet().encrypt(plain_key.strip().encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise CredentialCryptoError("Failed to decrypt credential (wrong key or corrupted data)") from e


def key_hint(plain_key: str) -> str:
    """Return last 4 characters for safe UI display (••••1234)."""
    cleaned = plain_key.strip()
    if len(cleaned) <= 4:
        return "••••"
    return f"••••{cleaned[-4:]}"


def mask_hint(hint: Optional[str]) -> str:
    if not hint:
        return "••••"
    if hint.startswith("••••"):
        return hint
    return f"••••{hint[-4:]}" if len(hint) >= 4 else "••••"


# Shape returned to API consumers (never contains the raw key)
def public_credential_view(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("id"),
        "provider": row.get("provider"),
        "key_hint": mask_hint(row.get("key_hint")),
        "is_enabled": row.get("is_enabled", True),
        "priority": row.get("priority", 100),
        "preferred_model": row.get("preferred_model"),
        "last_tested_at": row.get("last_tested_at"),
        "last_test_status": row.get("last_test_status"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }
