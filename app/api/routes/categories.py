from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentEmployeeOrAdminDep, DBSession
from app.schemas.category import CategoryCreate, CategoryListItem, CategoryRead, CategoryUpdate
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta, PaginationParams
from app.services.category_service import CategoryService

public_router = APIRouter(prefix="/categories", tags=["categories"])
admin_router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])


@public_router.get("", response_model=PaginatedResponse[CategoryListItem])
async def list_categories(
    pagination: Annotated[PaginationParams, Depends()],
    session: DBSession,
) -> PaginatedResponse[CategoryListItem]:
    categories, total = await CategoryService(session).list_active(pagination)
    return PaginatedResponse[CategoryListItem](
        message="Categories retrieved successfully",
        data=[CategoryListItem.from_model(category) for category in categories],
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )


@admin_router.post(
    "",
    response_model=ApiResponse[CategoryRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    payload: CategoryCreate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[CategoryRead]:
    category = await CategoryService(session).create(payload, current_user)
    return ApiResponse[CategoryRead](
        message="Category created successfully",
        data=CategoryRead.from_model(category),
    )


@admin_router.put("/{category_id}", response_model=ApiResponse[CategoryRead])
async def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[CategoryRead]:
    category = await CategoryService(session).update(category_id, payload, current_user)
    return ApiResponse[CategoryRead](
        message="Category updated successfully",
        data=CategoryRead.from_model(category),
    )


@admin_router.delete("/{category_id}", response_model=ApiResponse[CategoryRead])
async def delete_category(
    category_id: UUID,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[CategoryRead]:
    category = await CategoryService(session).deactivate(category_id, current_user)
    return ApiResponse[CategoryRead](
        message="Category deactivated successfully",
        data=CategoryRead.from_model(category),
    )
