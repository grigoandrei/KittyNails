"""add japanese manicure nail type and make design_tier_id optional

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-08 22:45:00.000000

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Japanese Manicure nail type and make design_tier_id nullable on
    appointments (Japanese Manicure doesn't use design tiers)."""
    # Add the Japanese Manicure nail type
    now = datetime.now(timezone.utc)
    op.execute(
        sa.text(
            "INSERT INTO nail_types (id, name, price, duration_minutes, sort_order, is_active, created_at, updated_at) "
            "VALUES (gen_random_uuid(), 'Japanese Manicure', 30, 60, 0, true, :now, :now)"
        ).bindparams(now=now)
    )

    # Make design_tier_id nullable so Japanese Manicure appointments don't need one
    op.alter_column('appointments', 'design_tier_id',
                    existing_type=sa.Uuid(),
                    nullable=True)


def downgrade() -> None:
    """Remove Japanese Manicure and make design_tier_id required again."""
    # Delete any appointments for Japanese Manicure (they have no design tier)
    op.execute(
        "DELETE FROM appointments WHERE nail_type_id IN "
        "(SELECT id FROM nail_types WHERE name = 'Japanese Manicure')"
    )
    # Remove null design_tier_id appointments before making column non-nullable
    op.execute("DELETE FROM appointments WHERE design_tier_id IS NULL")

    op.alter_column('appointments', 'design_tier_id',
                    existing_type=sa.Uuid(),
                    nullable=False)

    op.execute("DELETE FROM nail_types WHERE name = 'Japanese Manicure'")
