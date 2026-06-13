"""switch to Cohere embeddings 1024 dims

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00
"""

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


def upgrade() -> None:
    op.drop_column("articles", "embedding")
    op.drop_column("topics", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(1024), nullable=True))
    op.add_column("topics", sa.Column("embedding", Vector(1024), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "embedding")
    op.drop_column("topics", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(768), nullable=True))
    op.add_column("topics", sa.Column("embedding", Vector(768), nullable=True))
