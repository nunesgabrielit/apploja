from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, StringConstraints

from app.models.enums import FulfillmentType, OrderStatus, PaymentStatus

OrderNotesStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]


class OrderCreateRequest(BaseModel):
    fulfillment_type: FulfillmentType
    address_id: UUID | None = None
    notes: OrderNotesStr | None = None


class AssignEmployeeRequest(BaseModel):
    assigned_employee_id: UUID


class AdminOrderListFilters(BaseModel):
    order_status: OrderStatus | None = None
    payment_status: PaymentStatus | None = None
    fulfillment_type: FulfillmentType | None = None
    user_id: UUID | None = None
    assigned_employee_id: UUID | None = None


class OrderItemResponse(BaseModel):
    id: UUID
    product_item_id: UUID
    internal_code_snapshot: str
    name_snapshot: str
    unit_price: Decimal
    quantity: int
    total_item: Decimal
    created_at: datetime

    @classmethod
    def from_model(cls, item: object) -> "OrderItemResponse":
        return cls(
            id=item.id,
            product_item_id=item.product_item_id,
            internal_code_snapshot=item.internal_code_snapshot,
            name_snapshot=item.name_snapshot,
            unit_price=item.unit_price,
            quantity=item.quantity,
            total_item=item.total_item,
            created_at=item.created_at,
        )


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    address_id: UUID | None
    fulfillment_type: FulfillmentType
    order_status: OrderStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    shipping_price: Decimal
    discount: Decimal
    total: Decimal
    notes: str | None
    assigned_employee_id: UUID | None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, order: object) -> "OrderResponse":
        return cls(
            id=order.id,
            user_id=order.user_id,
            address_id=order.address_id,
            fulfillment_type=order.fulfillment_type,
            order_status=order.order_status,
            payment_status=order.payment_status,
            subtotal=order.subtotal,
            shipping_price=order.shipping_price,
            discount=order.discount,
            total=order.total,
            notes=order.notes,
            assigned_employee_id=order.assigned_employee_id,
            items=[OrderItemResponse.from_model(item) for item in order.items],
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class OrderListItem(BaseModel):
    id: UUID
    fulfillment_type: FulfillmentType
    order_status: OrderStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    shipping_price: Decimal
    discount: Decimal
    total: Decimal
    total_items: int
    created_at: datetime

    @classmethod
    def from_model(cls, order: object) -> "OrderListItem":
        return cls(
            id=order.id,
            fulfillment_type=order.fulfillment_type,
            order_status=order.order_status,
            payment_status=order.payment_status,
            subtotal=order.subtotal,
            shipping_price=order.shipping_price,
            discount=order.discount,
            total=order.total,
            total_items=sum(item.quantity for item in order.items),
            created_at=order.created_at,
        )


class AdminOrderListResponse(BaseModel):
    id: UUID
    user_id: UUID
    assigned_employee_id: UUID | None
    fulfillment_type: FulfillmentType
    order_status: OrderStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    shipping_price: Decimal
    discount: Decimal
    total: Decimal
    total_items: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, order: object) -> "AdminOrderListResponse":
        return cls(
            id=order.id,
            user_id=order.user_id,
            assigned_employee_id=order.assigned_employee_id,
            fulfillment_type=order.fulfillment_type,
            order_status=order.order_status,
            payment_status=order.payment_status,
            subtotal=order.subtotal,
            shipping_price=order.shipping_price,
            discount=order.discount,
            total=order.total,
            total_items=sum(item.quantity for item in order.items),
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class OrderStatusHistoryResponse(BaseModel):
    id: UUID
    order_id: UUID
    previous_status: OrderStatus | None
    new_status: OrderStatus
    changed_by_user_id: UUID | None
    created_at: datetime

    @classmethod
    def from_model(cls, history: object) -> "OrderStatusHistoryResponse":
        return cls(
            id=history.id,
            order_id=history.order_id,
            previous_status=history.previous_status,
            new_status=history.new_status,
            changed_by_user_id=history.changed_by_user_id,
            created_at=history.created_at,
        )


class EmployeePerformanceItem(BaseModel):
    employee_id: UUID
    employee_name: str
    employee_email: str
    processed_orders: int
    assigned_orders: int
    completed_orders: int
    total_sold: Decimal
