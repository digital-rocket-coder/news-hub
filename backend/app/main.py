from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

sys.stderr.write("IMPORT: fastapi\n"); sys.stderr.flush()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.stderr.write("IMPORT: app.api modules\n"); sys.stderr.flush()
from app.api import articles, digest, graph, sources, topics

sys.stderr.write("IMPORT: config/database/models\n"); sys.stderr.flush()
from app.config import settings
from app.database import engine
from app.models import Base

sys.stderr.write("IMPORT: scheduler\n"); sys.stderr.flush()
from app.services.scheduler import start_scheduler, stop_scheduler

sys.stderr.write("IMPORT: all done, creating app\n"); sys.stderr.flush()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import traceback
    try:
        sys.stderr.write("STARTUP: connecting to DB...\n"); sys.stderr.flush()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        sys.stderr.write("STARTUP: DB ready, starting scheduler...\n"); sys.stderr.flush()
        start_scheduler()
        sys.stderr.write("STARTUP: done.\n"); sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"STARTUP ERROR: {e}\n"); sys.stderr.flush()
        traceback.print_exc()
        raise
    yield
    stop_scheduler()


app = FastAPI(title="News Hub API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(digest.router, prefix="/api")
app.include_router(graph.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
