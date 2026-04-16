"""phase 7 operational audit

Revision ID: 20260411_0007
Revises: 20260411_0006
Create Date: 2026-04-11 21:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260411_0007"
down_revision: str | None = "20260411_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

stock_movement_type_enum = postgresql.ENUM(
    "sale",
    "manual_adjustment",
    "cancellation",
    "return",
    name="stock_movement_type_enum",
    create_type=False,
)

stock_movement_source_enum = postgresql.ENUM(
    "order",
    "admin",
    "system",
    name="stock_movement_source_enum",
    create_type=False,
)

order_status_enum = postgresql.ENUM(
    "waiting_payment",
    "paid",
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
    name="order_status_enum",
    create_type=False,
)


def upgrade() -> None:
    stock_movement_type_enum.create(op.get_bind(), checkfirst=True)
    stock_movement_source_enum.create(op.get_bind(), checkfirst=True)

    op.execute(
        """
        UPDATE stock_movements
        SET movement_type = CASE
            WHEN movement_type = 'payment_approved_sale' THEN 'sale'
            WHEN movement_type IN ('sale', 'manual_adjustment', 'cancellation', 'return') THEN movement_type
            ELSE 'manual_adjustment'
        END
        """
    )

    op.alter_column(
        "stock_movements",
        "movement_type",
        existing_type=sa.String(length=50),
        type_=stock_movement_type_enum,
        postgresql_using="movement_type::stock_movement_type_enum",
        nullable=False,
    )

    op.add_column(
        "stock_movements",
        sa.Column(
            "source",
            stock_movement_source_enum,
            nullable=False,
            server_default=sa.text("'system'"),
        ),
    )
    op.add_column(
        "stock_movements",
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("performed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_stock_movements_performed_by_user_id_users"),
        "stock_movements",
        "users",
        ["performed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_stock_movements_reference_id"),
        "stock_movements",
        ["reference_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_movements_performed_by_user_id"),
        "stock_movements",
        ["performed_by_user_id"],
        unique=False,
    )
    op.alter_column("stock_movements", "source", server_default=None)

    op.create_table(
        "order_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_status", order_status_enum, nullable=True),
        sa.Column("new_status", order_status_enum, nullable=False),
        sa.Column("changed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_status_history_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_user_id"],
            ["users.id"],
            name=op.f("fk_order_status_history_changed_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_status_history")),
    )
    op.create_index(
        op.f("ix_order_status_history_order_id"),
        "order_status_history",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_order_status_history_changed_by_user_id"),
        "order_status_history",
        ["changed_by_user_id"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity", sa.String(length=80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_audit_logs_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity"), "audit_logs", ["entity"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)

    op.create_index(op.f("ix_orders_order_status"), "orders", ["order_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_order_status"), table_name="orders")

    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_order_status_history_changed_by_user_id"), table_name="order_status_history")
    op.drop_index(op.f("ix_order_status_history_order_id"), table_name="order_status_history")
    op.drop_table("order_status_history")

    op.drop_index(op.f("ix_stock_movements_performed_by_user_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_reference_id"), table_name="stock_movements")
    op.drop_constraint(
        op.f("fk_stock_movements_performed_by_user_id_users"),
        "stock_movements",
        type_="foreignkey",
    )
    op.drop_column("stock_movements", "performed_by_user_id")
    op.drop_column("stock_movements", "reference_id")
    op.drop_column("stock_movements", "source")

    op.alter_column(
        "stock_movements",
        "movement_type",
        existing_type=stock_movement_type_enum,
        type_=sa.String(length=50),
        postgresql_using="movement_type::text",
        nullable=False,
    )

    stock_movement_source_enum.drop(op.get_bind(), checkfirst=True)
    stock_movement_type_enum.drop(op.get_bind(), checkfirst=True)
