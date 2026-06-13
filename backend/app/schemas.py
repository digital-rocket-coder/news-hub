from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models import SourceType, TopicType, TrendDirection


# ── Source ──────────────────────────────────────────────────────────────────

class SourceCreate(BaseModel):
    url: str
    name: str
    category: str | None = None
    poll_interval: int = 3600


class SourceUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    poll_interval: int | None = None
    is_active: bool | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: SourceType
    url: str
    name: str
    category: str | None
    poll_interval: int
    last_polled_at: datetime | None
    is_active: bool
    created_at: datetime


# ── Article ──────────────────────────────────────────────────────────────────

class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    title: str
    url: str
    published_at: datetime | None
    fetched_at: datetime
    description: str | None
    summary: str | None
    is_read: bool
    is_bookmarked: bool
    source_name: str | None = None


class ArticleUpdate(BaseModel):
    is_read: bool | None = None
    is_bookmarked: bool | None = None


# ── Topic ────────────────────────────────────────────────────────────────────

class TopicCreate(BaseModel):
    name: str
    keywords: str | None = None


class TopicUpdate(BaseModel):
    name: str | None = None
    keywords: str | None = None
    is_muted: bool | None = None


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: TopicType
    keywords: str | None
    is_muted: bool
    trend: TrendDirection | None
    created_at: datetime
    article_count: int = 0
    unread_count: int = 0


class TopicWithArticles(TopicOut):
    articles: list[ArticleOut] = []


# ── Trends ───────────────────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    period_start: datetime
    weight: int


class TopicTrendOut(BaseModel):
    topic_id: int
    topic_name: str
    direction: TrendDirection | None
    points: list[TrendPoint]


# ── Graph ────────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: int
    name: str
    article_count: int
    trend: TrendDirection | None
    is_muted: bool


class GraphEdge(BaseModel):
    source: int
    target: int
    strength: float


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ── Digest ───────────────────────────────────────────────────────────────────

class DigestTopicItem(BaseModel):
    topic: TopicOut
    key_articles: list[ArticleOut]
    summary: str | None = None


class DigestOut(BaseModel):
    period_label: str
    days_away: int
    items: list[DigestTopicItem]


# ── Cluster review ───────────────────────────────────────────────────────────

class ClusterCandidate(BaseModel):
    cluster_id: int
    suggested_name: str
    article_count: int
    sample_titles: list[str]


class ClusterConfirm(BaseModel):
    cluster_id: int
    name: str
    accept: bool = True
