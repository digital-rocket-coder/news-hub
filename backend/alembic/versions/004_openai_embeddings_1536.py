"""switch back to OpenAI embeddings 1536 dims

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00
"""

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


def upgrade() -> None:
    op.drop_column("articles", "embedding")
    op.drop_column("topics", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(1536), nullable=True))
    op.add_column("topics", sa.Column("embedding", Vector(1536), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "embedding")
    op.drop_column("topics", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(1024), nullable=True))
    op.add_column("topics", sa.Column("embedding", Vector(1024), nullable=True))
