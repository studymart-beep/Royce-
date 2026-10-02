"""Embedding abstraction.

V1 uses a simple deterministic local embedding when no external embedding
provider is configured, so the memory system works offline/tests.
When the user has a Gemini key, we can call Gemini embedding models.

Dimension is fixed at 1536 to match the schema.
"""

from __future__ import annotations

import hashlib
import logging
import math
import struct
from typing import List, Optional

logger = logging.getLogger("royce.embeddings")

EMBEDDING_DIM = 1536


def _local_embed(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Deterministic pseudo-embedding for dev/tests (not semantic quality)."""
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: List[float] = []
    counter = 0
    while len(values) < dim:
        block = hashlib.sha256(seed + counter.to_bytes(4, "little")).digest()
        for i in range(0, len(block) - 3, 4):
            # map 4 bytes to float in [-1, 1]
            n = struct.unpack_from("<I", block, i)[0]
            values.append((n / 0xFFFFFFFF) * 2.0 - 1.0)
            if len(values) >= dim:
                break
        counter += 1
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


async def embed_text(text: str, *, api_key: Optional[str] = None, provider: str = "local") -> List[float]:
    """
    Return embedding vector for text.
    provider=local uses deterministic hash embedding (always available).
    Future: gemini / openai when credentials present.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return [0.0] * EMBEDDING_DIM

    if provider == "gemini" and api_key:
        try:
            return await _gemini_embed(cleaned, api_key)
        except Exception as e:
            logger.warning("Gemini embedding failed, falling back to local: %s", e)

    return _local_embed(cleaned)


async def _gemini_embed(text: str, api_key: str) -> List[float]:
    """Use Gemini embedding model when available."""
    from google import genai

    client = genai.Client(api_key=api_key)
    # text-embedding-004 outputs 768; we pad/truncate to 1536 for schema stability
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )
    values = list(result.embeddings[0].values)
    if len(values) < EMBEDDING_DIM:
        values = values + [0.0] * (EMBEDDING_DIM - len(values))
    else:
        values = values[:EMBEDDING_DIM]
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


async def embed_texts(texts: List[str], **kwargs) -> List[List[float]]:
    out = []
    for t in texts:
        out.append(await embed_text(t, **kwargs))
    return out
