"""Add the removal-only nail type

Revision ID: c9d0e1f2a3b4
Revises: a7b8c9d0e1f2
Create Date: 2026-11-14 15:00:00.000000

Clients can book just a removal. Its price equals the €15 deposit, so the
deposit covers it and nothing is left to pay at the studio.
"""

from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision = "c9d0e1f2a3b4"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "INSERT INTO nail_types (id, name, price, duration_minutes, sort_order, is_active, created_at, updated_at) "
            "VALUES (gen_random_uuid(), 'Nail Removal', 15, 30, 3, true, :now, :now)"
        ).bindparams(now=datetime.now(UTC))
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM appointments WHERE nail_type_id IN "
        "(SELECT id FROM nail_types WHERE name = 'Nail Removal')"
    )
    op.execute("DELETE FROM nail_types WHERE name = 'Nail Removal'")
