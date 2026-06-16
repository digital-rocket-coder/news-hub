"""switch back to openai embeddings 1536 dims (no-op: DB already at correct state from migration 004)

Revision ID: 006
Revises: 005
Create Date: 2026-06-15
"""
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
