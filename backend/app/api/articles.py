from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Article, Source
from app.schemas import ArticleOut, ArticleUpdate

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
    q = select(Article).options(joinedload(Article.source)).order_by(Article.published_at.desc())
    if is_read is not None:
        q = q.where(Article.is_read == is_read)
    if is_bookmarked is not None:
        q = q.where(Article.is_bookmarked == is_bookmarked)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return [_to_out(a) for a in result.scalars().all()]


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
