"""add distance-based shipping module

Revision ID: 20260412_0008
Revises: 20260411_0007
Create Date: 2026-04-12 12:00:00
"""

from collections.abc import Sequence
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260412_0008"
down_revision: str | None = "20260411_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("addresses", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("addresses", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))

    op.create_table(
        "shipping_store_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_name", sa.String(length=255), nullable=False),
        sa.Column("zip_code", sa.String(length=8), nullable=False),
        sa.Column("street", sa.String(length=255), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("complement", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
            "length(zip_code) = 8",
            name=op.f("ck_shipping_store_configs_shipping_store_configs_zip_code_length"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shipping_store_configs")),
    )
    op.create_index(
        op.f("ix_shipping_store_configs_is_active"),
        "shipping_store_configs",
        ["is_active"],
        unique=False,
    )

    op.create_table(
        "shipping_distance_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("max_distance_km", sa.Numeric(6, 2), nullable=False),
        sa.Column("shipping_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("estimated_time_text", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
            "max_distance_km > 0",
            name=op.f("ck_shipping_distance_rules_shipping_distance_rules_distance_positive"),
        ),
        sa.CheckConstraint(
            "shipping_price >= 0",
            name=op.f("ck_shipping_distance_rules_shipping_distance_rules_price_non_negative"),
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name=op.f("ck_shipping_distance_rules_shipping_distance_rules_sort_order_non_negative"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shipping_distance_rules")),
    )
    op.create_index(
        op.f("ix_shipping_distance_rules_is_active"),
        "shipping_distance_rules",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shipping_distance_rules_max_distance_km"),
        "shipping_distance_rules",
        ["max_distance_km"],
        unique=False,
    )

    shipping_distance_rules_table = sa.table(
        "shipping_distance_rules",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("rule_name", sa.String(length=255)),
        sa.column("max_distance_km", sa.Numeric(6, 2)),
        sa.column("shipping_price", sa.Numeric(10, 2)),
        sa.column("estimated_time_text", sa.Text()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        shipping_distance_rules_table,
        [
            {
                "id": uuid.uuid4(),
                "rule_name": "Entrega ate 2 km",
                "max_distance_km": 2,
                "shipping_price": 5,
                "estimated_time_text": "Entrega local",
                "sort_order": 1,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "rule_name": "Entrega ate 4 km",
                "max_distance_km": 4,
                "shipping_price": 7,
                "estimated_time_text": "Entrega local",
                "sort_order": 2,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "rule_name": "Entrega ate 6 km",
                "max_distance_km": 6,
                "shipping_price": 7,
                "estimated_time_text": "Entrega local",
                "sort_order": 3,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "rule_name": "Entrega ate 8 km",
                "max_distance_km": 8,
                "shipping_price": 10,
                "estimated_time_text": "Entrega local",
                "sort_order": 4,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "rule_name": "Entrega ate 10 km",
                "max_distance_km": 10,
                "shipping_price": 11,
                "estimated_time_text": "Entrega local",
                "sort_order": 5,
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_shipping_distance_rules_max_distance_km"), table_name="shipping_distance_rules")
    op.drop_index(op.f("ix_shipping_distance_rules_is_active"), table_name="shipping_distance_rules")
    op.drop_table("shipping_distance_rules")

    op.drop_index(op.f("ix_shipping_store_configs_is_active"), table_name="shipping_store_configs")
    op.drop_table("shipping_store_configs")

    op.drop_column("addresses", "longitude")
    op.drop_column("addresses", "latitude")
