from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Article, ArticleTopic, Topic, TopicLink, TopicType
from app.services.llm import generate_topic_name

logger = logging.getLogger(__name__)

_clustering_lock = asyncio.Lock()


async def run_clustering(db: AsyncSession) -> int:
    """Cluster recent embedded articles into topics. Returns number of topics created/updated."""
    if _clustering_lock.locked():
        logger.info("Clustering already running, skipping.")
        return 0
    async with _clustering_lock:
        return await _do_clustering(db)


async def _do_clustering(db: AsyncSession) -> int:
    import numpy as np
    from sklearn.cluster import HDBSCAN
    from sklearn.preprocessing import normalize

    # 1. Load recent articles with embeddings (last 7 days only to limit memory)
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(Article.id, Article.title, Article.embedding)
        .where(Article.embedding.is_not(None))
        .where(Article.published_at >= cutoff)
    )
    rows = result.all()
    if len(rows) < settings.HDBSCAN_MIN_CLUSTER_SIZE:
        logger.info("Not enough embedded articles (%d) for clustering.", len(rows))
        return 0

    ids = [r.id for r in rows]
    titles = [r.title for r in rows]
    embeddings = np.array([r.embedding for r in rows], dtype=np.float32)
    embeddings_norm = normalize(embeddings)

    # 2. Cluster
    clusterer = HDBSCAN(
        min_cluster_size=settings.HDBSCAN_MIN_CLUSTER_SIZE,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels: np.ndarray = clusterer.fit_predict(embeddings_norm)

    unique_labels = sorted(set(labels.tolist()) - {-1})
    if not unique_labels:
        logger.info("HDBSCAN found no clusters.")
        return 0

    # 3. Remove old auto topics and article_topics
    existing_auto = await db.execute(select(Topic.id).where(Topic.type == TopicType.auto))
    auto_ids = [r[0] for r in existing_auto.all()]
    if auto_ids:
        await db.execute(delete(Topic).where(Topic.id.in_(auto_ids)))

    # 4. Build new topics
    new_topics: list[Topic] = []
    cluster_article_map: dict[int, list[int]] = defaultdict(list)

    for idx, label in enumerate(labels.tolist()):
        if label == -1:
            continue
        cluster_article_map[label].append(idx)

    for label in unique_labels:
        idxs = cluster_article_map[label]
        cluster_embeddings = embeddings[idxs]
        centroid = cluster_embeddings.mean(axis=0).tolist()
        sample_titles = [titles[i] for i in idxs[:10]]

        name = await generate_topic_name(sample_titles)

        topic = Topic(
            name=name,
            type=TopicType.auto,
            embedding=centroid,
            cluster_id=label,
        )
        db.add(topic)
        new_topics.append((topic, label))

    await db.flush()  # get topic IDs

    # 5. Link articles → topics
    for topic, label in new_topics:
        for idx in cluster_article_map[label]:
            db.add(ArticleTopic(article_id=ids[idx], topic_id=topic.id, confidence=1.0))

    # 6. Rebuild TopicLink (co-occurrence)
    await db.execute(delete(TopicLink))
    topic_objs = [t for t, _ in new_topics]
    await _build_topic_links(db, topic_objs, embeddings, labels, cluster_article_map)

    await db.commit()
    logger.info("Clustering done: %d topics.", len(new_topics))
    return len(new_topics)


async def _build_topic_links(
    db: AsyncSession,
    topics: list[Topic],
    embeddings: np.ndarray,
    labels: np.ndarray,
    cluster_article_map: dict[int, list[int]],
) -> None:
    """Create TopicLink rows based on cosine similarity between topic centroids."""
    if len(topics) < 2:
        return

    centroids = np.array([t.embedding for t in topics], dtype=np.float32)
    centroids_norm = normalize(centroids)
    sim_matrix = centroids_norm @ centroids_norm.T  # cosine similarity

    for i in range(len(topics)):
        for j in range(i + 1, len(topics)):
            strength = float(sim_matrix[i, j])
            if strength > 0.3:  # only meaningful connections
                db.add(TopicLink(
                    topic_a_id=topics[i].id,
                    topic_b_id=topics[j].id,
                    strength=round(strength, 4),
                ))
