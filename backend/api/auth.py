"""Auth-related routes (identity is verified via JWT dependency)."""

from __future__ import annotations

from fastapi import APIRouter

from api.deps import CurrentUser
from database.supabase import get_service_client

router = APIRouter()


@router.get("/me")
async def me(user: CurrentUser):
    client = get_service_client()
    profile = (
        client.table("profiles")
        .select("id, email, display_name, avatar_url, created_at")
        .eq("id", user.user_id)
        .maybe_single()
        .execute()
    )
    data = profile.data or {
        "id": user.user_id,
        "email": user.email,
        "display_name": None,
        "avatar_url": None,
    }
    return data
