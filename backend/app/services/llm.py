from __future__ import annotations

import logging

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


async def _complete(prompt: str, max_tokens: int = 256) -> str:
    msg = await _get_client().messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


async def generate_topic_name(sample_titles: list[str]) -> str:
    """Generate a concise topic name from a list of article titles."""
    titles_block = "\n".join(f"- {t}" for t in sample_titles[:10])
    prompt = (
        "You are naming a news topic cluster. Given these article titles, "
        "output ONLY a short topic name (2–5 words, title case, no punctuation).\n\n"
        f"{titles_block}"
    )
    try:
        return await _complete(prompt, max_tokens=32)
    except Exception as exc:
        logger.warning("LLM topic name failed: %s", exc)
        return sample_titles[0][:60] if sample_titles else "Unnamed Topic"


async def generate_article_summary(title: str, text: str) -> str:
    """Generate a 1–2 sentence summary for an article."""
    prompt = (
        "Summarize the following news article in 1–2 sentences. "
        "Be factual and concise. Output only the summary.\n\n"
        f"Title: {title}\n\n{text[:4000]}"
    )
    try:
        return await _complete(prompt, max_tokens=128)
    except Exception as exc:
        logger.warning("LLM summary failed: %s", exc)
        return ""


async def generate_topic_summary(topic_name: str, article_titles: list[str]) -> str:
    """Generate a digest-style paragraph summarising a topic's recent articles."""
    titles_block = "\n".join(f"- {t}" for t in article_titles[:15])
    prompt = (
        f"Write a 2–3 sentence summary of recent news about '{topic_name}'. "
        f"Use these headlines as context. Be concise.\n\n{titles_block}"
    )
    try:
        return await _complete(prompt, max_tokens=200)
    except Exception as exc:
        logger.warning("LLM topic summary failed: %s", exc)
        return ""
