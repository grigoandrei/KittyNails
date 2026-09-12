"""Add needs_removal flag to appointments

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-12 15:10:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Client requested removal of existing nails — a flat price surcharge.
    # server_default false so existing rows backfill cleanly and the column is
    # NOT NULL.
    op.add_column(
        "appointments",
        sa.Column(
            "needs_removal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("appointments", "needs_removal")
