"""Add monthly_set_models and link appointments to them

Revision ID: b8c9d0e1f2a3
Revises: c9d0e1f2a3b4
Create Date: 2026-11-14 12:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b8c9d0e1f2a3"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monthly_set_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("image_key", sa.String(512), nullable=False),
        sa.Column("price", sa.Numeric(8, 2), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "monthly_set_model_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monthly_set_models.id"),
            nullable=True,
        ),
    )
    # monthly set bookings have no nail type.
    op.alter_column("appointments", "nail_type_id", nullable=True)

    op.create_check_constraint(
        "ck_appointments_one_service",
        "appointments",
        "(nail_type_id IS NOT NULL) <> (monthly_set_model_id IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_appointments_monthly_set_no_tier",
        "appointments",
        "monthly_set_model_id IS NULL OR design_tier_id IS NULL",
    )
    # A model can be held by at most one live appointment.
    op.create_index(
        "uq_appointments_monthly_set_active",
        "appointments",
        ["monthly_set_model_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('PENDING_PAYMENT', 'BOOKED', 'COMPLETED')"
        ),
    )


def downgrade() -> None:
    op.drop_index("uq_appointments_monthly_set_active", table_name="appointments")
    op.drop_constraint("ck_appointments_monthly_set_no_tier", "appointments", type_="check")
    op.drop_constraint("ck_appointments_one_service", "appointments", type_="check")
    # monthly set appointments have no nail type, so they can't survive the downgrade.
    op.execute("DELETE FROM appointments WHERE monthly_set_model_id IS NOT NULL")
    op.alter_column("appointments", "nail_type_id", nullable=False)
    op.drop_column("appointments", "monthly_set_model_id")
    op.drop_table("monthly_set_models")
