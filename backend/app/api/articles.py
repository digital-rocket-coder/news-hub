from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload

from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.models import Article, Source
from app.schemas import ArticleOut, ArticleUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["articles"])


def _to_out(article: Article) -> ArticleOut:
    out = ArticleOut.model_validate(article)
    out.source_name = article.source.name if article.source else None
    return out


@router.get("/", response_model=list[ArticleOut])
async def list_articles(
    is_read: bool | None = Query(None),
    is_bookmarked: bool | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Article).options(
        defer(Article.embedding),
        joinedload(Article.source),
    ).order_by(Article.published_at.desc())
    if is_read is not None:
        q = q.where(Article.is_read == is_read)
    if is_bookmarked is not None:
        q = q.where(Article.is_bookmarked == is_bookmarked)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return [_to_out(a) for a in result.scalars().all()]


@router.get("/stats")
async def article_stats(db: AsyncSession = Depends(get_db)):
    """Debug: count total articles and those with embeddings."""
    total = await db.scalar(select(func.count()).select_from(Article))
    with_emb = await db.scalar(
        select(func.count()).select_from(Article).where(Article.embedding.is_not(None))
    )
    return {
        "total": total,
        "with_embedding": with_emb,
        "without_embedding": total - with_emb,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dims": settings.EMBEDDING_DIMS,
    }


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Article).options(joinedload(Article.source)).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, "Article not found.")
    return _to_out(article)


@router.patch("/{article_id}", response_model=ArticleOut)
async def update_article(article_id: int, body: ArticleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Article).options(joinedload(Article.source)).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, "Article not found.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(article, k, v)
    await db.commit()
    await db.refresh(article)
    return _to_out(article)


@router.post("/embed-pending", status_code=202)
async def embed_pending_articles(background_tasks: BackgroundTasks):
    """Embed all articles that have no embedding yet, then run clustering."""
    if settings.EMBEDDING_PROVIDER != "local" and not settings.OPENAI_API_KEY:
        raise HTTPException(400, "OPENAI_API_KEY is not configured.")
    background_tasks.add_task(_embed_pending_task)
    return {"detail": "Embedding job started in background."}


async def _embed_pending_task() -> None:
    from app.services import embeddings, clustering, trends

    BATCH = 50
    MAX_CONSECUTIVE_ERRORS = 3
    total_done = 0
    total_failed = 0
    consecutive_errors = 0

    while True:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Article)
                .where(Article.embedding.is_(None))
                .limit(BATCH)
            )
            batch = list(result.scalars().all())

        if not batch:
            break

        texts = [f"{a.title}. {a.description or a.full_text or ''}" for a in batch]
        try:
            vectors = await embeddings.embed_texts(texts)
            consecutive_errors = 0
        except Exception as exc:
            logger.error("Batch embed failed: %s", exc)
            total_failed += len(batch)
            consecutive_errors += 1
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.error("Too many consecutive errors — aborting embed-pending.")
                return
            await asyncio.sleep(5)
            continue

        async with AsyncSessionLocal() as db:
            for article, vec in zip(batch, vectors):
                obj = await db.get(Article, article.id)
                if obj:
                    obj.embedding = vec
            await db.commit()

        total_done += len(batch)
        logger.info("Embedded %d articles so far (%d failed)", total_done, total_failed)
        await asyncio.sleep(0.3)

    logger.info("Embed-pending done: %d embedded, %d failed", total_done, total_failed)

    async with AsyncSessionLocal() as db:
        await clustering.run_clustering(db)
    async with AsyncSessionLocal() as db:
        await trends.calculate_trends(db)
    logger.info("Pipeline complete after embed-pending.")


@router.post("/mark-all-read", status_code=200)
async def mark_all_read(topic_id: int | None = Query(None), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import update
    from app.models import ArticleTopic

    if topic_id is not None:
        subq = select(ArticleTopic.article_id).where(ArticleTopic.topic_id == topic_id)
        await db.execute(
            update(Article).where(Article.id.in_(subq)).values(is_read=True)
        )
    else:
        await db.execute(update(Article).values(is_read=True))
    await db.commit()
    return {"detail": "Marked as read."}
