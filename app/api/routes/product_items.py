from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentEmployeeOrAdminDep, DBSession
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.product_item import (
    ProductItemCreate,
    ProductItemListFilters,
    ProductItemListItem,
    ProductItemPriceUpdate,
    ProductItemRead,
    ProductItemStockUpdate,
    ProductItemUpdate,
)
from app.services.product_item_service import ProductItemService

public_router = APIRouter(prefix="/product-items", tags=["product-items"])
admin_router = APIRouter(prefix="/admin/product-items", tags=["admin-product-items"])


@public_router.get("", response_model=PaginatedResponse[ProductItemListItem])
async def list_product_items(
    filters: Annotated[ProductItemListFilters, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    session: DBSession,
) -> PaginatedResponse[ProductItemListItem]:
    items, total = await ProductItemService(session).list_active(filters, pagination)
    return PaginatedResponse[ProductItemListItem](
        message="Product items retrieved successfully",
        data=[ProductItemListItem.from_model(item) for item in items],
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )


@public_router.get("/{item_id}", response_model=ApiResponse[ProductItemRead])
async def get_product_item(item_id: UUID, session: DBSession) -> ApiResponse[ProductItemRead]:
    item = await ProductItemService(session).get_public_by_id(item_id)
    return ApiResponse[ProductItemRead](
        message="Product item retrieved successfully",
        data=ProductItemRead.from_model(item),
    )


@admin_router.post(
    "",
    response_model=ApiResponse[ProductItemRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_product_item(
    payload: ProductItemCreate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ProductItemRead]:
    item = await ProductItemService(session).create(payload, current_user)
    return ApiResponse[ProductItemRead](
        message="Product item created successfully",
        data=ProductItemRead.from_model(item),
    )


@admin_router.put("/{item_id}", response_model=ApiResponse[ProductItemRead])
async def update_product_item(
    item_id: UUID,
    payload: ProductItemUpdate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ProductItemRead]:
    item = await ProductItemService(session).update(item_id, payload, current_user)
    return ApiResponse[ProductItemRead](
        message="Product item updated successfully",
        data=ProductItemRead.from_model(item),
    )


@admin_router.patch("/{item_id}/stock", response_model=ApiResponse[ProductItemRead])
async def update_product_item_stock(
    item_id: UUID,
    payload: ProductItemStockUpdate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ProductItemRead]:
    item = await ProductItemService(session).update_stock(item_id, payload, current_user)
    return ApiResponse[ProductItemRead](
        message="Product item stock updated successfully",
        data=ProductItemRead.from_model(item),
    )


@admin_router.patch("/{item_id}/price", response_model=ApiResponse[ProductItemRead])
async def update_product_item_price(
    item_id: UUID,
    payload: ProductItemPriceUpdate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ProductItemRead]:
    item = await ProductItemService(session).update_price(item_id, payload, current_user)
    return ApiResponse[ProductItemRead](
        message="Product item price updated successfully",
        data=ProductItemRead.from_model(item),
    )


@admin_router.delete("/{item_id}", response_model=ApiResponse[ProductItemRead])
async def delete_product_item(
    item_id: UUID,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ProductItemRead]:
    item = await ProductItemService(session).deactivate(item_id, current_user)
    return ApiResponse[ProductItemRead](
        message="Product item deactivated successfully",
        data=ProductItemRead.from_model(item),
    )
