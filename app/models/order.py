from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import FulfillmentType, OrderStatus, PaymentStatus

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.order_item import OrderItem
    from app.models.order_status_history import OrderStatusHistory
    from app.models.payment import Payment
    from app.models.stock_movement import StockMovement
    from app.models.user import User


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="orders_subtotal_non_negative"),
        CheckConstraint("shipping_price >= 0", name="orders_shipping_price_non_negative"),
        CheckConstraint("discount >= 0", name="orders_discount_non_negative"),
        CheckConstraint("total >= 0", name="orders_total_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    address_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("addresses.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    assigned_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    fulfillment_type: Mapped[FulfillmentType] = mapped_column(
        Enum(
            FulfillmentType,
            name="fulfillment_type_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    order_status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=OrderStatus.WAITING_PAYMENT,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="payment_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="orders",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    address: Mapped[Address | None] = relationship(
        back_populates="orders",
        lazy="selectin",
    )
    assigned_employee: Mapped[User | None] = relationship(
        back_populates="assigned_orders",
        foreign_keys=[assigned_employee_id],
        lazy="selectin",
    )
    created_by_user: Mapped[User | None] = relationship(
        back_populates="created_orders",
        foreign_keys=[created_by_user_id],
        lazy="selectin",
    )
    updated_by_user: Mapped[User | None] = relationship(
        back_populates="updated_orders",
        foreign_keys=[updated_by_user_id],
        lazy="selectin",
    )
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItem.created_at.asc()",
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="order",
        lazy="selectin",
        order_by="Payment.created_at.desc()",
    )
    stock_movements: Mapped[list[StockMovement]] = relationship(
        back_populates="order",
        lazy="selectin",
    )
    status_history: Mapped[list[OrderStatusHistory]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderStatusHistory.created_at.asc()",
    )
