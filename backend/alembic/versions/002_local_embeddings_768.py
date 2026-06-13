"""switch to local embeddings 768 dims

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00
"""

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


def upgrade() -> None:
    # Drop vector columns (no data yet) and recreate with 768 dims
    op.drop_column("articles", "embedding")
    op.drop_column("topics", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(768), nullable=True))
    op.add_column("topics", sa.Column("embedding", Vector(768), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "embedding")
    op.drop_column("topics", "embedding")
    op.add_column("articles", sa.Column("embedding", Vector(1536), nullable=True))
    op.add_column("topics", sa.Column("embedding", Vector(1536), nullable=True))
