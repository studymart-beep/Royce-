"""Tasks CRUD API."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.deps import CurrentUser
from database.supabase import get_service_client

router = APIRouter()


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    due_at: Optional[str] = None
    status: str = "todo"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[str] = None
    status: Optional[str] = None


@router.get("")
async def list_tasks(user: CurrentUser, status: Optional[str] = None):
    client = get_service_client()
    q = client.table("tasks").select("*").eq("user_id", user.user_id).order("created_at", desc=True)
    if status:
        q = q.eq("status", status)
    return {"tasks": (q.execute().data) or []}


@router.post("")
async def create_task(body: TaskCreate, user: CurrentUser):
    client = get_service_client()
    row = (
        client.table("tasks")
        .insert(
            {
                "user_id": user.user_id,
                "title": body.title,
                "description": body.description,
                "due_at": body.due_at,
                "status": body.status,
            }
        )
        .execute()
    )
    return row.data[0]


@router.get("/{task_id}")
async def get_task(task_id: str, user: CurrentUser):
    client = get_service_client()
    row = (
        client.table("tasks")
        .select("*")
        .eq("id", task_id)
        .eq("user_id", user.user_id)
        .maybe_single()
        .execute()
    )
    if not row.data:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Task not found"}})
    return row.data


@router.patch("/{task_id}")
async def update_task(task_id: str, body: TaskUpdate, user: CurrentUser):
    client = get_service_client()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return await get_task(task_id, user)
    result = (
        client.table("tasks")
        .update(updates)
        .eq("id", task_id)
        .eq("user_id", user.user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Task not found"}})
    return result.data[0]


@router.delete("/{task_id}")
async def delete_task(task_id: str, user: CurrentUser):
    client = get_service_client()
    client.table("tasks").delete().eq("id", task_id).eq("user_id", user.user_id).execute()
    return {"ok": True}
