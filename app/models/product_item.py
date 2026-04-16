from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.cart_item import CartItem
    from app.models.order_item import OrderItem
    from app.models.product import Product
    from app.models.stock_movement import StockMovement


class ProductItem(TimestampMixin, Base):
    __tablename__ = "product_items"
    __table_args__ = (
        CheckConstraint("price > 0", name="product_items_price_positive"),
        CheckConstraint("stock_current >= 0", name="product_items_stock_current_non_negative"),
        CheckConstraint("stock_minimum >= 0", name="product_items_stock_minimum_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    internal_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    connector_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    power: Mapped[str | None] = mapped_column(String(100), nullable=True)
    voltage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimum: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    product: Mapped[Product] = relationship(
        back_populates="items",
        lazy="selectin",
    )
    cart_items: Mapped[list[CartItem]] = relationship(
        back_populates="product_item",
        lazy="selectin",
    )
    order_items: Mapped[list[OrderItem]] = relationship(
        back_populates="product_item",
        lazy="selectin",
    )
    stock_movements: Mapped[list[StockMovement]] = relationship(
        back_populates="product_item",
        lazy="selectin",
    )
