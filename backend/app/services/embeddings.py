from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def _embed_openai(texts: list[str]) -> list[list[float]]:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    cleaned = [t[:12000] for t in texts]
    response = await client.embeddings.create(model=settings.EMBEDDING_MODEL, input=cleaned)
    response.data.sort(key=lambda d: d.index)
    return [d.embedding for d in response.data]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return await _embed_openai(texts)


async def embed_text(text: str) -> list[float]:
    results = await embed_texts([text])
    return results[0]
