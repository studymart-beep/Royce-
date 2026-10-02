"""File upload, extraction, chunking, embeddings."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from database.supabase import get_service_client
from memory.embeddings import embed_text, EMBEDDING_DIM

logger = logging.getLogger("royce.files")

BUCKET = "royce-files"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MAX_BYTES = 20 * 1024 * 1024


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += max(size - overlap, 1)
    return chunks


def extract_text(filename: str, mime: str, data: bytes) -> str:
    lower = (filename or "").lower()
    if mime.startswith("text/") or lower.endswith((".txt", ".csv", ".md")):
        return data.decode("utf-8", errors="replace")
    if lower.endswith(".pdf") or mime == "application/pdf":
        try:
            from io import BytesIO
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            logger.warning("PDF extract failed: %s", e)
            return ""
    if lower.endswith(".docx") or "wordprocessingml" in (mime or ""):
        try:
            from io import BytesIO
            import zipfile
            # minimal docx: word/document.xml text
            with zipfile.ZipFile(BytesIO(data)) as z:
                xml = z.read("word/document.xml").decode("utf-8", errors="replace")
            return re.sub(r"<[^>]+>", " ", xml)
        except Exception as e:
            logger.warning("DOCX extract failed: %s", e)
            return ""
    # images: no OCR in V1
    return ""


async def upload_and_process(
    user_id: str,
    filename: str,
    content_type: str,
    data: bytes,
) -> Dict[str, Any]:
    if len(data) > MAX_BYTES:
        raise ValueError(f"File exceeds {MAX_BYTES // (1024*1024)}MB limit")
    client = get_service_client()
    file_id = str(uuid.uuid4())
    path = f"{user_id}/{file_id}/{filename}"

    # metadata row first
    row = (
        client.table("files")
        .insert(
            {
                "id": file_id,
                "user_id": user_id,
                "filename": filename,
                "mime_type": content_type,
                "size_bytes": len(data),
                "storage_path": path,
                "status": "processing",
            }
        )
        .execute()
    )

    try:
        client.storage.from_(BUCKET).upload(
            path,
            data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
    except Exception as e:
        client.table("files").update({"status": "failed", "error_message": str(e)}).eq("id", file_id).eq("user_id", user_id).execute()
        raise

    text = extract_text(filename, content_type, data)
    if not text.strip():
        client.table("files").update({"status": "ready", "metadata": {"note": "no extractable text"}}).eq("id", file_id).eq("user_id", user_id).execute()
        return (row.data or [{}])[0] | {"status": "ready"}

    chunks = _chunk_text(text)
    chunk_rows = []
    for idx, ch in enumerate(chunks):
        emb = await embed_text(ch)
        chunk_rows.append(
            {
                "file_id": file_id,
                "user_id": user_id,
                "chunk_index": idx,
                "content": ch,
                "embedding": emb,
            }
        )
    if chunk_rows:
        # batch insert
        for i in range(0, len(chunk_rows), 50):
            client.table("file_chunks").insert(chunk_rows[i : i + 50]).execute()

    client.table("files").update(
        {"status": "ready", "metadata": {"chunks": len(chunks)}}
    ).eq("id", file_id).eq("user_id", user_id).execute()

    updated = (
        client.table("files")
        .select("*")
        .eq("id", file_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    return updated.data or {}


async def list_files(user_id: str) -> List[Dict[str, Any]]:
    client = get_service_client()
    result = (
        client.table("files")
        .select("id, filename, mime_type, size_bytes, status, error_message, metadata, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    return result.data or []


async def delete_file(user_id: str, file_id: str) -> bool:
    client = get_service_client()
    row = (
        client.table("files")
        .select("storage_path")
        .eq("id", file_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not row.data:
        return False
    path = row.data.get("storage_path")
    try:
        if path:
            client.storage.from_(BUCKET).remove([path])
    except Exception:
        logger.exception("storage delete failed")
    client.table("files").delete().eq("id", file_id).eq("user_id", user_id).execute()
    return True


async def search_file_chunks(
    user_id: str,
    query: str,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """Document RAG — separate from personal memories."""
    if not query.strip():
        return []
    vector = await embed_text(query)
    client = get_service_client()
    try:
        result = client.rpc(
            "match_file_chunks",
            {
                "query_embedding": vector,
                "match_user_id": user_id,
                "match_count": limit,
                "match_threshold": 0.2,
            },
        ).execute()
        return result.data or []
    except Exception as e:
        logger.warning("match_file_chunks RPC missing: %s", e)
        # fallback: recent chunks text filter not available — return empty
        return []
