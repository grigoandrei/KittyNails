"""remove short nail type, keep only regular and extensions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-08 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove the 'Short' nail type. Only Regular and Extensions remain.
    Update durations: Regular=90min, Extensions=150min.
    Any appointments referencing Short must be handled before running this
    migration (reassign or delete them)."""
    # Delete any appointments that reference the Short nail type
    op.execute(
        "DELETE FROM appointments WHERE nail_type_id IN "
        "(SELECT id FROM nail_types WHERE name = 'Short')"
    )
    # Remove the Short nail type
    op.execute("DELETE FROM nail_types WHERE name = 'Short'")
    # Update sort orders and durations: Regular=1 (90min), Extensions=2 (150min)
    op.execute("UPDATE nail_types SET sort_order = 1, duration_minutes = 90 WHERE name = 'Regular'")
    op.execute("UPDATE nail_types SET sort_order = 2, duration_minutes = 150 WHERE name = 'Extensions'")


def downgrade() -> None:
    """Re-insert the Short nail type and restore original durations."""
    import uuid
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    short_id = str(uuid.uuid4())
    op.execute(
        f"INSERT INTO nail_types (id, name, price, duration_minutes, sort_order, is_active, created_at, updated_at) "
        f"VALUES ('{short_id}', 'Short', 30, 60, 1, true, '{now}', '{now}')"
    )
    # Restore original sort orders and durations
    op.execute("UPDATE nail_types SET sort_order = 2, duration_minutes = 75 WHERE name = 'Regular'")
    op.execute("UPDATE nail_types SET sort_order = 3, duration_minutes = 120 WHERE name = 'Extensions'")
