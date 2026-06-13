from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ArticleTopic, Topic, TopicLink
from app.schemas import GraphEdge, GraphNode, GraphOut

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/", response_model=GraphOut)
async def get_graph(db: AsyncSession = Depends(get_db)):
    topics_result = await db.execute(
        select(Topic).where(Topic.is_muted == False)
    )
    topics = topics_result.scalars().all()

    nodes: list[GraphNode] = []
    for topic in topics:
        count_r = await db.execute(
            select(func.count()).select_from(ArticleTopic).where(ArticleTopic.topic_id == topic.id)
        )
        nodes.append(GraphNode(
            id=topic.id,
            name=topic.name,
            article_count=count_r.scalar_one(),
            trend=topic.trend,
            is_muted=topic.is_muted,
        ))

    links_result = await db.execute(
        select(TopicLink).where(
            TopicLink.topic_a_id.in_([n.id for n in nodes]),
            TopicLink.topic_b_id.in_([n.id for n in nodes]),
        )
    )
    edges = [
        GraphEdge(source=link.topic_a_id, target=link.topic_b_id, strength=link.strength)
        for link in links_result.scalars().all()
    ]

    return GraphOut(nodes=nodes, edges=edges)
