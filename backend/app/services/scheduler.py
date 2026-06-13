from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.connectors.rss import RSSConnector
from app.database import AsyncSessionLocal
from app.models import Article, Source, SourceType
from app.services import clustering, embeddings, trends

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_rss_connector = RSSConnector()


async def poll_source(source_id: int) -> None:
    async with AsyncSessionLocal() as db:
        source = await db.get(Source, source_id)
        if not source or not source.is_active:
            return

        logger.info("Polling source %d: %s", source.id, source.url)
        connector: RSSConnector = _rss_connector  # only RSS for now

        try:
            fetched = await connector.fetch(source.url)
        except Exception as exc:
            logger.error("Fetch error for source %d: %s", source.id, exc)
            return

        new_articles: list[Article] = []
        for item in fetched:
            exists = await db.execute(select(Article.id).where(Article.url == item.url))
            if exists.scalar_one_or_none():
                continue
            article = Article(
                source_id=source.id,
                title=item.title,
                url=item.url,
                description=item.description,
                full_text=item.full_text,
                published_at=item.published_at,
            )
            db.add(article)
            new_articles.append(article)

        if new_articles:
            await db.flush()
            # Embed new articles
            texts = [
                f"{a.title}. {a.description or a.full_text or ''}"
                for a in new_articles
            ]
            try:
                vectors = await embeddings.embed_texts(texts)
                for article, vec in zip(new_articles, vectors):
                    article.embedding = vec
            except Exception as exc:
                logger.error("Embedding error: %s", exc)

        source.last_polled_at = datetime.now(timezone.utc)
        await db.commit()

        if new_articles:
            logger.info("Added %d new articles from source %d.", len(new_articles), source.id)
            await _run_pipeline()


async def _run_pipeline() -> None:
    """Run clustering + trend update after new articles arrive."""
    async with AsyncSessionLocal() as db:
        await clustering.run_clustering(db)
    async with AsyncSessionLocal() as db:
        await trends.calculate_trends(db)


async def poll_all_sources() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Source.id).where(Source.is_active == True))
        source_ids = [r[0] for r in result.all()]
    await asyncio.gather(*(poll_source(sid) for sid in source_ids))


def start_scheduler() -> None:
    scheduler.add_job(
        poll_all_sources,
        "interval",
        seconds=settings.RSS_POLL_INTERVAL_SECONDS,
        id="poll_all_sources",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),  # run immediately on startup
    )
    scheduler.start()
    logger.info("Scheduler started (interval=%ds).", settings.RSS_POLL_INTERVAL_SECONDS)


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
