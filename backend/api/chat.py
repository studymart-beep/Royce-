"""Chat API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.deps import CurrentUser
from schemas.chat import ChatRequest, ChatResponse
from services.chat import ChatService
from ai.router import AIRouter
from ai.providers import build_provider_instances
from services.provider_credentials import resolve_credentials_for_user

router = APIRouter()

_providers = build_provider_instances()
_ai_router = AIRouter(_providers, credential_resolver=resolve_credentials_for_user)
_chat_service = ChatService(_ai_router)


@router.post("", response_model=ChatResponse)
async def post_chat(
    body: ChatRequest,
    user: CurrentUser,
    request: Request,
) -> ChatResponse:
    request_id = getattr(request.state, "request_id", None)
    return await _chat_service.chat(
        user_id=user.user_id,
        request=body,
        request_id=request_id,
    )
