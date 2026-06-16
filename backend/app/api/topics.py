from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload, selectinload

from app.database import get_db
from app.models import Article, ArticleTopic, Source, Topic, TopicTrend, TopicType
from app.schemas import (
    ClusterCandidate,
    ClusterConfirm,
    TopicCreate,
    TopicOut,
    TopicTrendOut,
    TopicUpdate,
    TopicWithArticles,
    TrendPoint,
)
from app.services import clustering, trends

router = APIRouter(prefix="/topics", tags=["topics"])


async def _topic_out(topic: Topic, db: AsyncSession) -> TopicOut:
    count_result = await db.execute(
        select(func.count()).select_from(ArticleTopic).where(ArticleTopic.topic_id == topic.id)
    )
    article_count = count_result.scalar_one()

    unread_result = await db.execute(
        select(func.count())
        .select_from(ArticleTopic)
        .join(Article, Article.id == ArticleTopic.article_id)
        .where(ArticleTopic.topic_id == topic.id, Article.is_read == False)
    )
    unread_count = unread_result.scalar_one()

    out = TopicOut.model_validate(topic)
    out.article_count = article_count
    out.unread_count = unread_count
    return out


# ── Static routes (must be before /{topic_id} wildcards) ────────────────────

@router.get("/", response_model=list[TopicOut])
async def list_topics(
    include_muted: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(Topic).order_by(Topic.name)
    if not include_muted:
        q = q.where(Topic.is_muted == False)
    result = await db.execute(q)
    topics = result.scalars().all()

    if not topics:
        return []

    topic_ids = [t.id for t in topics]

    # Single query for total article counts
    counts_result = await db.execute(
        select(ArticleTopic.topic_id, func.count().label("cnt"))
        .where(ArticleTopic.topic_id.in_(topic_ids))
        .group_by(ArticleTopic.topic_id)
    )
    counts = {row.topic_id: row.cnt for row in counts_result}

    # Single query for unread counts
    unread_result = await db.execute(
        select(ArticleTopic.topic_id, func.count().label("cnt"))
        .join(Article, Article.id == ArticleTopic.article_id)
        .where(ArticleTopic.topic_id.in_(topic_ids), Article.is_read == False)
        .group_by(ArticleTopic.topic_id)
    )
    unread = {row.topic_id: row.cnt for row in unread_result}

    out = []
    for t in topics:
        o = TopicOut.model_validate(t)
        o.article_count = counts.get(t.id, 0)
        o.unread_count = unread.get(t.id, 0)
        out.append(o)
    return out


@router.post("/", response_model=TopicOut, status_code=201)
async def create_topic(body: TopicCreate, db: AsyncSession = Depends(get_db)):
    topic = Topic(name=body.name, keywords=body.keywords, type=TopicType.manual)
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return await _topic_out(topic, db)


@router.get("/clusters/pending", response_model=list[ClusterCandidate])
async def pending_clusters(db: AsyncSession = Depends(get_db)):
    """Return auto clusters awaiting user confirmation (topics with no user edits)."""
    import logging as _log
    _log.getLogger(__name__).info("pending_clusters called")
    try:
        result = await db.execute(
            select(Topic).where(Topic.type == TopicType.auto).order_by(Topic.name)
        )
        topics = result.scalars().all()
        candidates: list[ClusterCandidate] = []
        for t in topics:
            arts = await db.execute(
                select(Article.title)
                .join(ArticleTopic, ArticleTopic.article_id == Article.id)
                .where(ArticleTopic.topic_id == t.id)
                .limit(5)
            )
            titles = [r[0] for r in arts.all()]
            count_r = await db.execute(
                select(func.count()).select_from(ArticleTopic).where(ArticleTopic.topic_id == t.id)
            )
            candidates.append(ClusterCandidate(
                cluster_id=t.id,
                suggested_name=t.name,
                article_count=count_r.scalar_one(),
                sample_titles=titles,
            ))
        return candidates
    except Exception as exc:
        import traceback
        _log.getLogger(__name__).error("pending_clusters error: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/clusters/confirm", status_code=200)
async def confirm_cluster(body: ClusterConfirm, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, body.cluster_id)
    if not topic:
        raise HTTPException(404, "Topic not found.")
    if not body.accept:
        await db.delete(topic)
    else:
        topic.name = body.name
    await db.commit()
    return {"detail": "ok"}


@router.post("/reset-auto", status_code=200)
async def reset_auto_topics(db: AsyncSession = Depends(get_db)):
    """Delete all auto-generated topics and re-run clustering from scratch."""
    result = await db.execute(
        select(func.count()).select_from(Topic).where(Topic.type == TopicType.auto)
    )
    count = result.scalar_one()
    await db.execute(delete(Topic).where(Topic.type == TopicType.auto))
    await db.commit()

    import asyncio
    from app.database import AsyncSessionLocal
    from app.services import clustering as cl, trends as tr

    async def run():
        async with AsyncSessionLocal() as s:
            await cl.run_clustering(s)
        async with AsyncSessionLocal() as s:
            await tr.calculate_trends(s)

    asyncio.create_task(run())
    return {"deleted": count, "detail": "Auto topics deleted; re-clustering started."}


@router.post("/recluster", status_code=202)
async def trigger_recluster(db: AsyncSession = Depends(get_db)):
    """Manually trigger a re-clustering + trend update."""
    import asyncio
    from app.database import AsyncSessionLocal
    from app.services import clustering as cl, trends as tr

    async def run():
        async with AsyncSessionLocal() as s:
            await cl.run_clustering(s)
        async with AsyncSessionLocal() as s:
            await tr.calculate_trends(s)

    asyncio.create_task(run())
    return {"detail": "Re-clustering triggered."}


# ── Parametric routes ────────────────────────────────────────────────────────

@router.get("/{topic_id}", response_model=TopicWithArticles)
async def get_topic(
    topic_id: int,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found.")

    arts_result = await db.execute(
        select(Article)
        .options(defer(Article.embedding), joinedload(Article.source))
        .join(ArticleTopic, ArticleTopic.article_id == Article.id)
        .where(ArticleTopic.topic_id == topic_id)
        .order_by(Article.published_at.desc())
        .limit(limit)
        .offset(offset)
    )
    articles = arts_result.scalars().all()

    from app.schemas import ArticleOut
    out = TopicWithArticles.model_validate(topic)
    out.article_count = len(articles)
    out.unread_count = sum(1 for a in articles if not a.is_read)
    out.articles = [
        ArticleOut.model_validate(a) for a in articles
    ]
    for art_out, art in zip(out.articles, articles):
        art_out.source_name = art.source.name if art.source else None
    return out


@router.patch("/{topic_id}", response_model=TopicOut)
async def update_topic(topic_id: int, body: TopicUpdate, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(topic, k, v)
    await db.commit()
    await db.refresh(topic)
    return await _topic_out(topic, db)


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found.")
    await db.delete(topic)
    await db.commit()


@router.get("/{topic_id}/trends", response_model=TopicTrendOut)
async def get_topic_trends(topic_id: int, db: AsyncSession = Depends(get_db)):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found.")
    result = await db.execute(
        select(TopicTrend)
        .where(TopicTrend.topic_id == topic_id)
        .order_by(TopicTrend.period_start)
    )
    points = [TrendPoint(period_start=r.period_start, weight=r.weight) for r in result.scalars()]
    return TopicTrendOut(
        topic_id=topic_id,
        topic_name=topic.name,
        direction=topic.trend,
        points=points,
    )
