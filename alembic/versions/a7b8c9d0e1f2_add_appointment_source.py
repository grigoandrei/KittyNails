"""Add source (web|instagram) to appointments

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-12 15:31:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # How the appointment was created. server_default "web" so existing rows
    # (all self-booked via the site) backfill correctly and the column is NOT NULL.
    op.add_column(
        "appointments",
        sa.Column(
            "source",
            sa.String(20),
            nullable=False,
            server_default="web",
        ),
    )


def downgrade() -> None:
    op.drop_column("appointments", "source")
