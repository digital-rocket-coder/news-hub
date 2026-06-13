"""
One-time script: embed all articles that don't have embeddings yet,
then trigger clustering + trends.
Run from backend/ with the venv active.
"""
import asyncio
import logging
from app.database import AsyncSessionLocal
from app.models import Article
from app.services.embeddings import embed_texts
from app.services.clustering import run_clustering
from app.services.trends import calculate_trends
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

BATCH = 50


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Article.id, Article.title, Article.description, Article.full_text)
            .where(Article.embedding.is_(None))
        )
        rows = result.all()

    log.info("Articles without embeddings: %d", len(rows))
    if not rows:
        log.info("Nothing to do.")
        return

    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        texts = [
            f"{r.title}. {r.description or r.full_text or ''}"[:12000]
            for r in batch
        ]
        log.info("Embedding batch %d/%d (%d articles)...",
                 i // BATCH + 1, (len(rows) + BATCH - 1) // BATCH, len(batch))
        try:
            vectors = await embed_texts(texts)
        except Exception as e:
            log.error("Embedding failed: %s", e)
            continue

        async with AsyncSessionLocal() as db:
            for row, vec in zip(batch, vectors):
                article = await db.get(Article, row.id)
                if article:
                    article.embedding = vec
            await db.commit()

    log.info("All embeddings done. Running clustering...")
    async with AsyncSessionLocal() as db:
        n = await run_clustering(db)
    log.info("Clustering done: %d topics.", n)

    log.info("Calculating trends...")
    async with AsyncSessionLocal() as db:
        await calculate_trends(db)
    log.info("Done! Open http://localhost:5173 and go to Topics.")


asyncio.run(main())
