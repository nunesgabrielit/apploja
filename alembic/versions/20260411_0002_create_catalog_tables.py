"""create catalog tables

Revision ID: 20260411_0002
Revises: 20260411_0001
Create Date: 2026-04-11 16:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260411_0002"
down_revision: str | None = "20260411_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_categories_name")),
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name_base", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_products_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
    )

    op.create_table(
        "product_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("internal_code", sa.String(length=100), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("connector_type", sa.String(length=100), nullable=True),
        sa.Column("power", sa.String(length=100), nullable=True),
        sa.Column("voltage", sa.String(length=100), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stock_minimum", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.CheckConstraint("price > 0", name=op.f("ck_product_items_product_items_price_positive")),
        sa.CheckConstraint(
            "stock_current >= 0",
            name=op.f("ck_product_items_product_items_stock_current_non_negative"),
        ),
        sa.CheckConstraint(
            "stock_minimum >= 0",
            name=op.f("ck_product_items_product_items_stock_minimum_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_items_product_id_products"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_items")),
        sa.UniqueConstraint("internal_code", name=op.f("uq_product_items_internal_code")),
        sa.UniqueConstraint("sku", name=op.f("uq_product_items_sku")),
    )

    op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)
    op.create_index(op.f("ix_products_name_base"), "products", ["name_base"], unique=False)
    op.create_index(op.f("ix_products_brand"), "products", ["brand"], unique=False)

    op.create_index(op.f("ix_product_items_product_id"), "product_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_product_items_name"), "product_items", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_product_items_name"), table_name="product_items")
    op.drop_index(op.f("ix_product_items_product_id"), table_name="product_items")
    op.drop_table("product_items")

    op.drop_index(op.f("ix_products_brand"), table_name="products")
    op.drop_index(op.f("ix_products_name_base"), table_name="products")
    op.drop_index(op.f("ix_products_category_id"), table_name="products")
    op.drop_table("products")

    op.drop_table("categories")
