from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentEmployeeOrAdminDep, DBSession
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.product import ProductCreate, ProductListFilters, ProductListItem, ProductRead, ProductUpdate
from app.services.product_service import ProductService

public_router = APIRouter(prefix="/products", tags=["products"])
admin_router = APIRouter(prefix="/admin/products", tags=["admin-products"])


@public_router.get("", response_model=PaginatedResponse[ProductListItem])
async def list_products(
    filters: Annotated[ProductListFilters, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    session: DBSession,
) -> PaginatedResponse[ProductListItem]:
    products, total = await ProductService(session).list_active(filters, pagination)
    return PaginatedResponse[ProductListItem](
        message="Products retrieved successfully",
        data=[ProductListItem.from_model(product) for product in products],
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )


@public_router.get("/{product_id}", response_model=ApiResponse[ProductRead])
async def get_product(product_id: UUID, session: DBSession) -> ApiResponse[ProductRead]:
    product = await ProductService(session).get_public_by_id(product_id)
    return ApiResponse[ProductRead](
        message="Product retrieved successfully",
        data=ProductRead.from_model(product),
    )


@admin_router.post(
    "",
    response_model=ApiResponse[ProductRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    payload: ProductCreate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ProductRead]:
    product = await ProductService(session).create(payload, current_user)
    return ApiResponse[ProductRead](
        message="Product created successfully",
        data=ProductRead.from_model(product),
    )


@admin_router.put("/{product_id}", response_model=ApiResponse[ProductRead])
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ProductRead]:
    product = await ProductService(session).update(product_id, payload, current_user)
    return ApiResponse[ProductRead](
        message="Product updated successfully",
        data=ProductRead.from_model(product),
    )


@admin_router.delete("/{product_id}", response_model=ApiResponse[ProductRead])
async def delete_product(
    product_id: UUID,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ProductRead]:
    product = await ProductService(session).deactivate(product_id, current_user)
    return ApiResponse[ProductRead](
        message="Product deactivated successfully",
        data=ProductRead.from_model(product),
    )
