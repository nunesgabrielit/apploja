from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CartStatus


class CartItemCreate(BaseModel):
    product_item_id: UUID
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartSummary(BaseModel):
    total_items: int
    subtotal: Decimal


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_item_id: UUID
    internal_code: str
    sku: str
    name: str
    product_name_base: str
    brand: str | None
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    available_stock: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, item: object) -> "CartItemResponse":
        line_total = item.unit_price * item.quantity
        return cls(
            id=item.id,
            product_item_id=item.product_item_id,
            internal_code=item.product_item.internal_code,
            sku=item.product_item.sku,
            name=item.product_item.name,
            product_name_base=item.product_item.product.name_base,
            brand=item.product_item.product.brand,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=line_total,
            available_stock=item.product_item.stock_current,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: CartStatus
    items: list[CartItemResponse]
    subtotal: Decimal
    total_items: int
    summary: CartSummary
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, cart: object) -> "CartResponse":
        items = [CartItemResponse.from_model(item) for item in cart.items]
        subtotal = sum((item.line_total for item in items), Decimal("0.00"))
        total_items = sum(item.quantity for item in items)

        return cls(
            id=cart.id,
            status=cart.status,
            items=items,
            subtotal=subtotal,
            total_items=total_items,
            summary=CartSummary(total_items=total_items, subtotal=subtotal),
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )
