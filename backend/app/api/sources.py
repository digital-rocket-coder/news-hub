from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Source
from app.schemas import SourceCreate, SourceOut, SourceUpdate
from app.services.scheduler import poll_source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/", response_model=list[SourceOut])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.created_at))
    return result.scalars().all()


@router.post("/", response_model=SourceOut, status_code=201)
async def create_source(body: SourceCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Source).where(Source.url == body.url))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Source with this URL already exists.")
    source = Source(**body.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    # Trigger an immediate poll in the background
    import asyncio
    asyncio.create_task(poll_source(source.id))
    return source


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    return source


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(source_id: int, body: SourceUpdate, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(source, k, v)
    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    await db.delete(source)
    await db.commit()


@router.post("/{source_id}/poll", status_code=202)
async def trigger_poll(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(404, "Source not found.")
    import asyncio
    asyncio.create_task(poll_source(source_id))
    return {"detail": "Poll triggered."}
