from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import (
    CurrentAdminDep,
    CurrentCustomerDep,
    CurrentEmployeeOrAdminDep,
    DBSession,
)
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.order import (
    AdminOrderListFilters,
    AdminOrderListResponse,
    AssignEmployeeRequest,
    OrderCreateRequest,
    OrderListItem,
    OrderResponse,
    OrderStatusHistoryResponse,
)
from app.services.order_service import OrderService

customer_router = APIRouter(prefix="/orders", tags=["orders"])
admin_router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])


@customer_router.post("", response_model=ApiResponse[OrderResponse], status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[OrderResponse]:
    order = await OrderService(session).create_from_cart(current_user, payload)
    return ApiResponse[OrderResponse](
        message="Order created successfully",
        data=OrderResponse.from_model(order),
    )


@customer_router.get("/me", response_model=PaginatedResponse[OrderListItem])
async def list_my_orders(
    pagination: Annotated[PaginationParams, Depends()],
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> PaginatedResponse[OrderListItem]:
    orders, total = await OrderService(session).list_my_orders(current_user, pagination)
    return PaginatedResponse[OrderListItem](
        message="Orders retrieved successfully",
        data=[OrderListItem.from_model(order) for order in orders],
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )


@customer_router.get("/me/{order_id}", response_model=ApiResponse[OrderResponse])
async def get_my_order(
    order_id: UUID,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[OrderResponse]:
    order = await OrderService(session).get_my_order(current_user, order_id)
    return ApiResponse[OrderResponse](
        message="Order retrieved successfully",
        data=OrderResponse.from_model(order),
    )


@admin_router.get("", response_model=PaginatedResponse[AdminOrderListResponse])
async def list_admin_orders(
    filters: Annotated[AdminOrderListFilters, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> PaginatedResponse[AdminOrderListResponse]:
    orders, total = await OrderService(session).list_admin_orders(filters, pagination)
    return PaginatedResponse[AdminOrderListResponse](
        message="Orders retrieved successfully",
        data=[AdminOrderListResponse.from_model(order) for order in orders],
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )


@admin_router.get("/{order_id}", response_model=ApiResponse[OrderResponse])
async def get_admin_order(
    order_id: UUID,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[OrderResponse]:
    order = await OrderService(session).get_admin_order(order_id)
    return ApiResponse[OrderResponse](
        message="Order retrieved successfully",
        data=OrderResponse.from_model(order),
    )


@admin_router.patch("/{order_id}/assign-employee", response_model=ApiResponse[OrderResponse])
async def assign_order_employee(
    order_id: UUID,
    payload: AssignEmployeeRequest,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[OrderResponse]:
    order = await OrderService(session).assign_employee(order_id, payload, current_user)
    return ApiResponse[OrderResponse](
        message="Order employee assigned successfully",
        data=OrderResponse.from_model(order),
    )


@admin_router.get("/{order_id}/history", response_model=ApiResponse[list[OrderStatusHistoryResponse]])
async def get_order_history(
    order_id: UUID,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[list[OrderStatusHistoryResponse]]:
    history = await OrderService(session).list_order_status_history(order_id)
    return ApiResponse[list[OrderStatusHistoryResponse]](
        message="Order status history retrieved successfully",
        data=[OrderStatusHistoryResponse.from_model(entry) for entry in history],
    )


@admin_router.post("/{order_id}/cancel", response_model=ApiResponse[OrderResponse])
async def cancel_order(
    order_id: UUID,
    session: DBSession,
    current_user: CurrentAdminDep,
    return_to_stock: bool = True,
) -> ApiResponse[OrderResponse]:
    order = await OrderService(session).cancel_order(
        order_id,
        current_user,
        return_to_stock=return_to_stock,
    )
    return ApiResponse[OrderResponse](
        message="Order cancelled successfully",
        data=OrderResponse.from_model(order),
    )
