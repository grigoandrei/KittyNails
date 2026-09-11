"""Add image_key to appointments for stored client nail photos

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-29 11:50:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # S3 object key of the client's uploaded nail photo. Nullable — Japanese
    # Manicure bookings have no photo, and older rows predate this feature.
    op.add_column(
        "appointments", sa.Column("image_key", sa.String(512), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("appointments", "image_key")
