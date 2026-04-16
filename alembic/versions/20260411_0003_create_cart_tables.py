"""create cart tables

Revision ID: 20260411_0003
Revises: 20260411_0002
Create Date: 2026-04-11 17:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260411_0003"
down_revision: str | None = "20260411_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

cart_status_enum = postgresql.ENUM(
    "active",
    "converted",
    "abandoned",
    name="cart_status_enum",
    create_type=False,
)


def upgrade() -> None:
    cart_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "carts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", cart_status_enum, nullable=False),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_carts_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_carts")),
    )

    op.create_table(
        "cart_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cart_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
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
        sa.CheckConstraint("quantity >= 1", name=op.f("ck_cart_items_cart_items_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["cart_id"],
            ["carts.id"],
            name=op.f("fk_cart_items_cart_id_carts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_item_id"],
            ["product_items.id"],
            name=op.f("fk_cart_items_product_item_id_product_items"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cart_items")),
        sa.UniqueConstraint(
            "cart_id",
            "product_item_id",
            name=op.f("uq_cart_items_cart_id_product_item_id"),
        ),
    )

    op.create_index(op.f("ix_carts_user_id"), "carts", ["user_id"], unique=False)
    op.create_index(op.f("ix_cart_items_cart_id"), "cart_items", ["cart_id"], unique=False)
    op.create_index(
        op.f("ix_cart_items_product_item_id"),
        "cart_items",
        ["product_item_id"],
        unique=False,
    )
    op.create_index(
        "uq_carts_active_user_id",
        "carts",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_carts_active_user_id", table_name="carts")
    op.drop_index(op.f("ix_cart_items_product_item_id"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_cart_id"), table_name="cart_items")
    op.drop_table("cart_items")

    op.drop_index(op.f("ix_carts_user_id"), table_name="carts")
    op.drop_table("carts")
    cart_status_enum.drop(op.get_bind(), checkfirst=True)
