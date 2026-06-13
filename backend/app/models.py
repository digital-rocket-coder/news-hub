from __future__ import annotations

import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base


class SourceType(str, enum.Enum):
    rss = "rss"


class TopicType(str, enum.Enum):
    auto = "auto"
    manual = "manual"


class TrendDirection(str, enum.Enum):
    rising = "rising"
    falling = "falling"
    stable = "stable"
    new = "new"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType), default=SourceType.rss)
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128))
    poll_interval: Mapped[int] = mapped_column(Integer, default=3600)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articles: Mapped[list[Article]] = relationship("Article", back_populates="source")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    description: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBEDDING_DIMS))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped[Source] = relationship("Source", back_populates="articles")
    article_topics: Mapped[list[ArticleTopic]] = relationship("ArticleTopic", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_source_id", "source_id"),
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[TopicType] = mapped_column(Enum(TopicType), default=TopicType.auto)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.EMBEDDING_DIMS))
    keywords: Mapped[str | None] = mapped_column(Text)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    trend: Mapped[TrendDirection | None] = mapped_column(Enum(TrendDirection))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cluster_id: Mapped[int | None] = mapped_column(Integer)

    article_topics: Mapped[list[ArticleTopic]] = relationship("ArticleTopic", back_populates="topic", cascade="all, delete-orphan")
    trends: Mapped[list[TopicTrend]] = relationship("TopicTrend", back_populates="topic", cascade="all, delete-orphan")


class ArticleTopic(Base):
    __tablename__ = "article_topics"

    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    article: Mapped[Article] = relationship("Article", back_populates="article_topics")
    topic: Mapped[Topic] = relationship("Topic", back_populates="article_topics")


class TopicTrend(Base):
    __tablename__ = "topic_trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=0)

    topic: Mapped[Topic] = relationship("Topic", back_populates="trends")

    __table_args__ = (
        UniqueConstraint("topic_id", "period_start", name="uq_topic_trend_period"),
        Index("ix_topic_trends_topic_id", "topic_id"),
    )


class TopicLink(Base):
    __tablename__ = "topic_links"

    topic_a_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    topic_b_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    strength: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint("topic_a_id", "topic_b_id", name="uq_topic_link"),
    )
