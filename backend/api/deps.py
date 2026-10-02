"""FastAPI dependencies: authentication and common utilities."""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import get_settings

logger = logging.getLogger("royce.auth")
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    def __init__(self, user_id: str, email: Optional[str] = None, access_token: str = ""):
        self.user_id = user_id
        self.email = email
        self.access_token = access_token


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> AuthenticatedUser:
    """
    Verify Supabase JWT and return the authenticated user.
    Never trust a client-supplied user_id.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Missing or invalid Authorization header",
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    settings = get_settings()

    try:
        from database.supabase import get_service_client

        client = get_service_client()
        # supabase-py auth.get_user validates the JWT against the project
        user_response = client.auth.get_user(token)
        user = user_response.user
        if user is None or not user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                    }
                },
            )
        return AuthenticatedUser(
            user_id=str(user.id),
            email=user.email,
            access_token=token,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("JWT verification failed: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Could not verify authentication token",
                }
            },
        ) from e


# Type alias for route signatures
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
