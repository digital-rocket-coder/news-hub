"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00
"""

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from app.config import settings


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("type", sa.String(32), nullable=False, server_default="rss"),
        sa.Column("url", sa.String(2048), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("poll_interval", sa.Integer, nullable=False, server_default="3600"),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id", ondelete="CASCADE")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("url", sa.String(2048), nullable=False, unique=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("full_text", sa.Text, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("embedding", Vector(settings.EMBEDDING_DIMS), nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_bookmarked", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_source_id", "articles", ["source_id"])

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("type", sa.String(32), nullable=False, server_default="auto"),
        sa.Column("embedding", Vector(settings.EMBEDDING_DIMS), nullable=True),
        sa.Column("keywords", sa.Text, nullable=True),
        sa.Column("is_muted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("trend", sa.String(32), nullable=True),
        sa.Column("cluster_id", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "article_topics",
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("topic_id", sa.Integer, sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
    )

    op.create_table(
        "topic_trends",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("topic_id", sa.Integer, sa.ForeignKey("topics.id", ondelete="CASCADE")),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("weight", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("topic_id", "period_start", name="uq_topic_trend_period"),
    )
    op.create_index("ix_topic_trends_topic_id", "topic_trends", ["topic_id"])

    op.create_table(
        "topic_links",
        sa.Column("topic_a_id", sa.Integer, sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("topic_b_id", sa.Integer, sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("strength", sa.Float, nullable=False, server_default="0.0"),
        sa.UniqueConstraint("topic_a_id", "topic_b_id", name="uq_topic_link"),
    )


def downgrade() -> None:
    op.drop_table("topic_links")
    op.drop_table("topic_trends")
    op.drop_table("article_topics")
    op.drop_table("topics")
    op.drop_table("articles")
    op.drop_table("sources")
