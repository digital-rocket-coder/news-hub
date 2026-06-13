"""switch to local fastembed 384 dims

Revision ID: 005
Revises: 004
Create Date: 2026-06-13
"""
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


def upgrade() -> None:
    op.drop_column("articles", "embedding")
    op.drop_column("topics", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(384), nullable=True))
    op.add_column("topics", sa.Column("embedding", Vector(384), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "embedding")
    op.drop_column("topics", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(1536), nullable=True))
    op.add_column("topics", sa.Column("embedding", Vector(1536), nullable=True))
