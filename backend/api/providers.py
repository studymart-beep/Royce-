"""Provider credentials API — never returns decrypted keys."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.deps import CurrentUser
from services import provider_credentials as pcs
from ai.providers import build_provider_instances
from ai.types import ProviderError

router = APIRouter()


class UpsertProviderBody(BaseModel):
    api_key: str = Field(..., min_length=8, max_length=512)
    preferred_model: Optional[str] = None
    priority: int = 100
    is_enabled: bool = True


class UpdateProviderMetaBody(BaseModel):
    preferred_model: Optional[str] = None
    priority: Optional[int] = None
    is_enabled: Optional[bool] = None


@router.get("")
async def list_providers(user: CurrentUser):
    return {"providers": await pcs.list_credentials(user.user_id)}


@router.put("/{provider}")
async def upsert_provider(provider: str, body: UpsertProviderBody, user: CurrentUser):
    allowed = {"gemini", "groq", "cerebras"}
    if provider not in allowed:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_PROVIDER", "message": f"Unknown provider {provider}"}})
    view = await pcs.upsert_credential(
        user.user_id,
        provider,
        body.api_key,
        preferred_model=body.preferred_model,
        priority=body.priority,
        is_enabled=body.is_enabled,
    )
    return view


@router.patch("/{provider}")
async def patch_provider(provider: str, body: UpdateProviderMetaBody, user: CurrentUser):
    view = await pcs.update_credential_meta(
        user.user_id,
        provider,
        preferred_model=body.preferred_model,
        priority=body.priority,
        is_enabled=body.is_enabled,
    )
    if not view:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Provider credential not found"}})
    return view


@router.delete("/{provider}")
async def delete_provider(provider: str, user: CurrentUser):
    await pcs.delete_credential(user.user_id, provider)
    return {"ok": True}


@router.post("/{provider}/test")
async def test_provider(provider: str, user: CurrentUser):
    creds = await pcs.resolve_credentials_for_user(user.user_id)
    if provider not in creds:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "No key configured"}})
    instances = build_provider_instances()
    if provider not in instances:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_PROVIDER", "message": "Unknown provider"}})
    try:
        resp = await instances[provider].generate(
            [{"role": "user", "content": "Reply with exactly: ok"}],
            api_key=creds[provider]["api_key"],
            model=creds[provider].get("preferred_model"),
            max_tokens=8,
            temperature=0,
        )
        return {"status": "ok", "provider": provider, "model": resp.model, "sample": (resp.content or "")[:80]}
    except ProviderError as e:
        return {"status": "error", "provider": provider, "error_type": e.error_type.value, "message": str(e)}
