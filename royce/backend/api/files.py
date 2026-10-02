"""Files API — upload, list, delete."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.deps import CurrentUser
from services import files as file_service

router = APIRouter()

ALLOWED = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/csv",
    "text/markdown",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
}


@router.get("")
async def list_files(user: CurrentUser):
    return {"files": await file_service.list_files(user.user_id)}


@router.post("")
async def upload_file(user: CurrentUser, file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail={"error": {"code": "EMPTY", "message": "Empty file"}})
    if len(data) > file_service.MAX_BYTES:
        raise HTTPException(status_code=400, detail={"error": {"code": "TOO_LARGE", "message": "Max 20MB"}})
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "upload.bin"
    try:
        row = await file_service.upload_and_process(
            user.user_id, filename, content_type, data
        )
        return row
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION", "message": str(e)}}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "UPLOAD_FAILED", "message": str(e)}}) from e


@router.delete("/{file_id}")
async def delete_file(file_id: str, user: CurrentUser):
    ok = await file_service.delete_file(user.user_id, file_id)
    if not ok:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "File not found"}})
    return {"ok": True}
