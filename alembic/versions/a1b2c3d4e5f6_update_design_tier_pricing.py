"""update design tier pricing and durations

Revision ID: a1b2c3d4e5f6
Revises: 19a839927e25
Create Date: 2026-08-05 23:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '19a839927e25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Design tiers represent additive price/duration on top of the nail type
    base cost. New logic:
      - Simple: no extra cost, no extra time (€0 / 0 min)
      - Medium: +€10, no extra time (€10 / 0 min)
      - Advanced: +€20, +30 min (€20 / 30 min)
    """
    op.execute(
        "UPDATE design_tiers SET price = 0, duration_minutes = 0 WHERE name = 'Simple'"
    )
    op.execute(
        "UPDATE design_tiers SET price = 10, duration_minutes = 0 WHERE name = 'Medium'"
    )
    op.execute(
        "UPDATE design_tiers SET price = 20, duration_minutes = 30 WHERE name = 'Advanced'"
    )


def downgrade() -> None:
    """Restore original seed values."""
    op.execute(
        "UPDATE design_tiers SET price = 10, duration_minutes = 15 WHERE name = 'Simple'"
    )
    op.execute(
        "UPDATE design_tiers SET price = 25, duration_minutes = 45 WHERE name = 'Medium'"
    )
    op.execute(
        "UPDATE design_tiers SET price = 45, duration_minutes = 90 WHERE name = 'Advanced'"
    )
