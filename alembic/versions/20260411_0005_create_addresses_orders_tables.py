"""create addresses and orders tables

Revision ID: 20260411_0005
Revises: 20260411_0004
Create Date: 2026-04-11 19:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260411_0005"
down_revision: str | None = "20260411_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

fulfillment_type_enum = postgresql.ENUM(
    "delivery",
    "pickup",
    name="fulfillment_type_enum",
    create_type=False,
)

order_status_enum = postgresql.ENUM(
    "waiting_payment",
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
    name="order_status_enum",
    create_type=False,
)

payment_status_enum = postgresql.ENUM(
    "pending",
    "authorized",
    "paid",
    "failed",
    "refunded",
    "cancelled",
    name="payment_status_enum",
    create_type=False,
)


def upgrade() -> None:
    fulfillment_type_enum.create(op.get_bind(), checkfirst=True)
    order_status_enum.create(op.get_bind(), checkfirst=True)
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_name", sa.String(length=255), nullable=False),
        sa.Column("zip_code", sa.String(length=8), nullable=False),
        sa.Column("street", sa.String(length=255), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("complement", sa.String(length=255), nullable=True),
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
            "length(zip_code) = 8",
            name=op.f("ck_addresses_addresses_zip_code_length"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_addresses_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_addresses")),
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fulfillment_type", fulfillment_type_enum, nullable=False),
        sa.Column("order_status", order_status_enum, nullable=False),
        sa.Column("payment_status", payment_status_enum, nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("shipping_price", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("discount", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.CheckConstraint("subtotal >= 0", name=op.f("ck_orders_orders_subtotal_non_negative")),
        sa.CheckConstraint(
            "shipping_price >= 0",
            name=op.f("ck_orders_orders_shipping_price_non_negative"),
        ),
        sa.CheckConstraint("discount >= 0", name=op.f("ck_orders_orders_discount_non_negative")),
        sa.CheckConstraint("total >= 0", name=op.f("ck_orders_orders_total_non_negative")),
        sa.ForeignKeyConstraint(
            ["address_id"],
            ["addresses.id"],
            name=op.f("fk_orders_address_id_addresses"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_employee_id"],
            ["users.id"],
            name=op.f("fk_orders_assigned_employee_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_orders_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name=op.f("fk_orders_updated_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_orders_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
    )

    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("internal_code_snapshot", sa.String(length=100), nullable=False),
        sa.Column("name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("total_item", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "quantity >= 1",
            name=op.f("ck_order_items_order_items_quantity_positive"),
        ),
        sa.CheckConstraint(
            "unit_price >= 0",
            name=op.f("ck_order_items_order_items_unit_price_non_negative"),
        ),
        sa.CheckConstraint(
            "total_item >= 0",
            name=op.f("ck_order_items_order_items_total_item_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_items_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_item_id"],
            ["product_items.id"],
            name=op.f("fk_order_items_product_item_id_product_items"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_items")),
    )

    op.create_index(op.f("ix_addresses_user_id"), "addresses", ["user_id"], unique=False)
    op.create_index(op.f("ix_addresses_zip_code"), "addresses", ["zip_code"], unique=False)
    op.create_index(op.f("ix_orders_address_id"), "orders", ["address_id"], unique=False)
    op.create_index(
        op.f("ix_orders_assigned_employee_id"),
        "orders",
        ["assigned_employee_id"],
        unique=False,
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)
    op.create_index(
        "ix_orders_status_filters",
        "orders",
        ["order_status", "payment_status", "fulfillment_type"],
        unique=False,
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(
        op.f("ix_order_items_product_item_id"),
        "order_items",
        ["product_item_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_order_items_product_item_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_orders_status_filters", table_name="orders")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_assigned_employee_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_address_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_addresses_zip_code"), table_name="addresses")
    op.drop_index(op.f("ix_addresses_user_id"), table_name="addresses")
    op.drop_table("addresses")

    payment_status_enum.drop(op.get_bind(), checkfirst=True)
    order_status_enum.drop(op.get_bind(), checkfirst=True)
    fulfillment_type_enum.drop(op.get_bind(), checkfirst=True)
