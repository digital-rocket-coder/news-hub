from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article, ArticleTopic, Topic, TopicTrend, TrendDirection

logger = logging.getLogger(__name__)

WEEKS_HISTORY = 8


async def calculate_trends(db: AsyncSession) -> None:
    """Compute weekly article counts per topic and update trend direction."""

    now = datetime.now(timezone.utc)
    topics_result = await db.execute(select(Topic.id))
    topic_ids = [r[0] for r in topics_result.all()]

    for topic_id in topic_ids:
        weekly_counts: list[int] = []

        for week_offset in range(WEEKS_HISTORY):
            week_end = now - timedelta(weeks=week_offset)
            week_start = now - timedelta(weeks=week_offset + 1)

            count_result = await db.execute(
                select(func.count())
                .select_from(ArticleTopic)
                .join(Article, Article.id == ArticleTopic.article_id)
                .where(
                    ArticleTopic.topic_id == topic_id,
                    Article.published_at >= week_start,
                    Article.published_at < week_end,
                )
            )
            count = count_result.scalar_one()
            weekly_counts.append(count)

            # Upsert trend point
            existing = await db.execute(
                select(TopicTrend).where(
                    TopicTrend.topic_id == topic_id,
                    TopicTrend.period_start == week_start,
                )
            )
            trend_row = existing.scalar_one_or_none()
            if trend_row:
                trend_row.weight = count
            else:
                db.add(TopicTrend(topic_id=topic_id, period_start=week_start, weight=count))

        # Determine direction from last 2 weeks vs 2 weeks before that
        current = sum(weekly_counts[:2])
        previous = sum(weekly_counts[2:4])
        total = sum(weekly_counts)

        direction: TrendDirection | None
        if total == 0:
            direction = None
        elif previous == 0 and current > 0:
            direction = TrendDirection.new
        elif current > previous * 1.3:
            direction = TrendDirection.rising
        elif current < previous * 0.7:
            direction = TrendDirection.falling
        else:
            direction = TrendDirection.stable

        topic_obj = await db.get(Topic, topic_id)
        if topic_obj:
            topic_obj.trend = direction

    await db.commit()
    logger.info("Trend calculation done for %d topics.", len(topic_ids))
