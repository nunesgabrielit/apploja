"""create shipping rules table

Revision ID: 20260411_0004
Revises: 20260411_0003
Create Date: 2026-04-11 18:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260411_0004"
down_revision: str | None = "20260411_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shipping_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("zip_code_start", sa.String(length=8), nullable=False),
        sa.Column("zip_code_end", sa.String(length=8), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("shipping_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("estimated_time_text", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "length(zip_code_start) = 8",
            name=op.f("ck_shipping_rules_shipping_rules_zip_code_start_length"),
        ),
        sa.CheckConstraint(
            "length(zip_code_end) = 8",
            name=op.f("ck_shipping_rules_shipping_rules_zip_code_end_length"),
        ),
        sa.CheckConstraint(
            "zip_code_start <= zip_code_end",
            name=op.f("ck_shipping_rules_shipping_rules_zip_code_range_valid"),
        ),
        sa.CheckConstraint(
            "shipping_price >= 0",
            name=op.f("ck_shipping_rules_shipping_rules_shipping_price_non_negative"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shipping_rules")),
    )

    op.create_index(op.f("ix_shipping_rules_is_active"), "shipping_rules", ["is_active"], unique=False)
    op.create_index(
        op.f("ix_shipping_rules_zip_code_end"),
        "shipping_rules",
        ["zip_code_end"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shipping_rules_zip_code_start"),
        "shipping_rules",
        ["zip_code_start"],
        unique=False,
    )
    op.create_index(
        "ix_shipping_rules_active_zip_range",
        "shipping_rules",
        ["is_active", "zip_code_start", "zip_code_end"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_shipping_rules_active_zip_range", table_name="shipping_rules")
    op.drop_index(op.f("ix_shipping_rules_zip_code_start"), table_name="shipping_rules")
    op.drop_index(op.f("ix_shipping_rules_zip_code_end"), table_name="shipping_rules")
    op.drop_index(op.f("ix_shipping_rules_is_active"), table_name="shipping_rules")
    op.drop_table("shipping_rules")
