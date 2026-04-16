"""create payments tables

Revision ID: 20260411_0006
Revises: 20260411_0005
Create Date: 2026-04-11 20:25:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260411_0006"
down_revision: str | None = "20260411_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

payment_provider_enum = postgresql.ENUM(
    "mercadopago",
    name="payment_provider_enum",
    create_type=False,
)

payment_method_enum = postgresql.ENUM(
    "pix",
    "card",
    name="payment_method_enum",
    create_type=False,
)

payment_status_enum = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    "authorized",
    "paid",
    "failed",
    "refunded",
    "cancelled",
    name="payment_status_enum",
    create_type=False,
)


def upgrade() -> None:
    op.execute("ALTER TYPE order_status_enum ADD VALUE IF NOT EXISTS 'paid'")
    op.execute("ALTER TYPE payment_status_enum ADD VALUE IF NOT EXISTS 'approved'")
    op.execute("ALTER TYPE payment_status_enum ADD VALUE IF NOT EXISTS 'rejected'")

    payment_provider_enum.create(op.get_bind(), checkfirst=True)
    payment_method_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", payment_provider_enum, nullable=False),
        sa.Column("method", payment_method_enum, nullable=False),
        sa.Column("external_id", sa.String(length=120), nullable=True),
        sa.Column("status", payment_status_enum, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("qr_code", sa.Text(), nullable=True),
        sa.Column("copy_paste_code", sa.Text(), nullable=True),
        sa.Column("provider_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.CheckConstraint("amount >= 0", name=op.f("ck_payments_payments_amount_non_negative")),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_payments_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
    )

    op.create_table(
        "stock_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("movement_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("previous_stock", sa.Integer(), nullable=False),
        sa.Column("new_stock", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_stock_movements_order_id_orders"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["payments.id"],
            name=op.f("fk_stock_movements_payment_id_payments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["product_item_id"],
            ["product_items.id"],
            name=op.f("fk_stock_movements_product_item_id_product_items"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stock_movements")),
    )

    op.create_index(op.f("ix_payments_order_id"), "payments", ["order_id"], unique=False)
    op.create_index(op.f("ix_payments_external_id"), "payments", ["external_id"], unique=True)
    op.create_index(
        "ix_payments_status_provider",
        "payments",
        ["status", "provider", "method"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_movements_product_item_id"),
        "stock_movements",
        ["product_item_id"],
        unique=False,
    )
    op.create_index(op.f("ix_stock_movements_order_id"), "stock_movements", ["order_id"], unique=False)
    op.create_index(
        op.f("ix_stock_movements_payment_id"),
        "stock_movements",
        ["payment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_stock_movements_payment_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_order_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_product_item_id"), table_name="stock_movements")
    op.drop_table("stock_movements")

    op.drop_index("ix_payments_status_provider", table_name="payments")
    op.drop_index(op.f("ix_payments_external_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_order_id"), table_name="payments")
    op.drop_table("payments")

    payment_method_enum.drop(op.get_bind(), checkfirst=True)
    payment_provider_enum.drop(op.get_bind(), checkfirst=True)
