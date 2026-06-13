from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return embeddings for a batch of texts (strips to 8191 tokens via truncation)."""
    if not texts:
        return []
    cleaned = [t[:12000] for t in texts]  # rough char limit well within token limit
    response = await _get_client().embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=cleaned,
    )
    response.data.sort(key=lambda d: d.index)
    return [d.embedding for d in response.data]


async def embed_text(text: str) -> list[float]:
    results = await embed_texts([text])
    return results[0]
