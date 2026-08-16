"""Add Stripe fields and PENDING_PAYMENT status to appointments

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-13 19:20:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns for Stripe integration
    op.add_column("appointments", sa.Column("stripe_session_id", sa.String(255), nullable=True))
    op.add_column(
        "appointments", sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True)
    )

    # Add PENDING_PAYMENT to the status enum
    # PostgreSQL requires explicit ALTER TYPE for enums
    op.execute("ALTER TYPE status ADD VALUE IF NOT EXISTS 'PENDING_PAYMENT' BEFORE 'BOOKED'")


def downgrade() -> None:
    op.drop_column("appointments", "stripe_payment_intent_id")
    op.drop_column("appointments", "stripe_session_id")
    # Note: PostgreSQL doesn't support removing enum values easily.
    # In downgrade, PENDING_PAYMENT appointments should be manually cleaned up.
