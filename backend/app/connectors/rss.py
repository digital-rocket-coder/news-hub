from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from app.connectors.base import BaseConnector, FetchedArticle

logger = logging.getLogger(__name__)


def _parse_date(entry: feedparser.FeedParserDict) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).astimezone(timezone.utc)
            except Exception:
                pass
    return None


def _clean_html(text: str | None) -> str | None:
    if not text:
        return None
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(text, "lxml").get_text(separator=" ", strip=True)
    except Exception:
        return text


class RSSConnector(BaseConnector):
    async def fetch(self, url: str) -> list[FetchedArticle]:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)

        if feed.bozo and not feed.entries:
            logger.warning("RSS parse error for %s: %s", url, feed.bozo_exception)
            return []

        articles: list[FetchedArticle] = []
        for entry in feed.entries:
            link = getattr(entry, "link", None) or getattr(entry, "id", None)
            title = getattr(entry, "title", None)
            if not link or not title:
                continue

            summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
            content = None
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].get("value")

            articles.append(
                FetchedArticle(
                    title=title.strip(),
                    url=link.strip(),
                    description=_clean_html(summary),
                    full_text=_clean_html(content or summary),
                    published_at=_parse_date(entry),
                )
            )

        return articles
