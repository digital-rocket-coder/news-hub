from __future__ import annotations

import asyncio
import logging

from app.config import settings

logger = logging.getLogger(__name__)

_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from fastembed import TextEmbedding
        logger.info("Loading local embedding model: %s", settings.EMBEDDING_MODEL)
        _local_model = TextEmbedding(settings.EMBEDDING_MODEL)
        logger.info("Local embedding model loaded.")
    return _local_model


async def _embed_local(texts: list[str]) -> list[list[float]]:
    loop = asyncio.get_event_loop()

    def _sync():
        model = _get_local_model()
        return [e.tolist() for e in model.embed(texts)]

    return await loop.run_in_executor(None, _sync)


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
    if settings.EMBEDDING_PROVIDER == "local":
        return await _embed_local(texts)
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return await _embed_openai(texts)


async def embed_text(text: str) -> list[float]:
    results = await embed_texts([text])
    return results[0]
