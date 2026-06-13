from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Article, ArticleTopic, Topic, TopicTrend, TrendDirection
from app.schemas import ArticleOut, DigestOut, DigestTopicItem, TopicOut
from app.services.llm import generate_topic_summary

router = APIRouter(prefix="/digest", tags=["digest"])

DIGEST_TOPIC_LIMIT = 7
ARTICLES_PER_TOPIC = 3


def _period_label(days_away: int) -> str:
    if days_away <= 1:
        return "Today"
    if days_away <= 7:
        return f"Last {days_away} days"
    if days_away <= 30:
        weeks = days_away // 7
        return f"Last {weeks} week{'s' if weeks > 1 else ''}"
    months = days_away // 30
    return f"Last {months} month{'s' if months > 1 else ''}"


@router.get("/", response_model=DigestOut)
async def get_digest(
    since_days: int = Query(7, ge=1, le=180),
    db: AsyncSession = Depends(get_db),
):
    """Return the adaptive digest for the given look-back window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    # Topics ordered by number of recent unread articles (proxy for importance)
    top_topics_q = (
        select(
            ArticleTopic.topic_id,
            func.count().label("cnt"),
        )
        .join(Article, Article.id == ArticleTopic.article_id)
        .join(Topic, Topic.id == ArticleTopic.topic_id)
        .where(
            Article.published_at >= cutoff,
            Article.is_read == False,
            Topic.is_muted == False,
        )
        .group_by(ArticleTopic.topic_id)
        .order_by(func.count().desc())
        .limit(DIGEST_TOPIC_LIMIT)
    )
    result = await db.execute(top_topics_q)
    topic_rows = result.all()

    items: list[DigestTopicItem] = []
    for topic_id, cnt in topic_rows:
        topic = await db.get(Topic, topic_id)
        if not topic:
            continue

        arts_result = await db.execute(
            select(Article)
            .options(joinedload(Article.source))
            .join(ArticleTopic, ArticleTopic.article_id == Article.id)
            .where(
                ArticleTopic.topic_id == topic_id,
                Article.published_at >= cutoff,
                Article.is_read == False,
            )
            .order_by(Article.published_at.desc())
            .limit(ARTICLES_PER_TOPIC)
        )
        articles = arts_result.scalars().all()

        total_count_r = await db.execute(
            select(func.count())
            .select_from(ArticleTopic)
            .where(ArticleTopic.topic_id == topic_id)
        )
        total_count = total_count_r.scalar_one()

        unread_count_r = await db.execute(
            select(func.count())
            .select_from(ArticleTopic)
            .join(Article, Article.id == ArticleTopic.article_id)
            .where(ArticleTopic.topic_id == topic_id, Article.is_read == False)
        )
        unread_count = unread_count_r.scalar_one()

        topic_out = TopicOut.model_validate(topic)
        topic_out.article_count = total_count
        topic_out.unread_count = unread_count

        article_outs: list[ArticleOut] = []
        for a in articles:
            a_out = ArticleOut.model_validate(a)
            a_out.source_name = a.source.name if a.source else None
            article_outs.append(a_out)

        titles = [a.title for a in articles]
        summary = await generate_topic_summary(topic.name, titles) if titles else None

        items.append(DigestTopicItem(topic=topic_out, key_articles=article_outs, summary=summary))

    return DigestOut(
        period_label=_period_label(since_days),
        days_away=since_days,
        items=items,
    )
