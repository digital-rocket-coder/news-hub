"""switch to local fastembed 384 dims (no-op: DB already at correct state from migration 004)

Revision ID: 005
Revises: 004
Create Date: 2026-06-13
"""
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
