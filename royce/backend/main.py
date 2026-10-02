"""Royce FastAPI application entrypoint."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from api import auth, chat, conversations, tasks, memories, providers, files

logger = logging.getLogger("royce")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.info("Royce backend starting (env=%s)", settings.environment)
    # Ensure tools are registered
    import tools  # noqa: F401
    yield
    logger.info("Royce backend shutting down")


app = FastAPI(
    title="Royce API",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled error request_id=%s", request_id)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"request_id": request_id},
            }
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "royce-backend", "version": "0.1.0"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(memories.router, prefix="/memories", tags=["memories"])
app.include_router(providers.router, prefix="/providers", tags=["providers"])
app.include_router(files.router, prefix="/files", tags=["files"])
