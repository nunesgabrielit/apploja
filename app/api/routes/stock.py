from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentEmployeeOrAdminDep, DBSession
from app.repositories.stock_movement_repository import StockMovementRepository
from app.schemas.common import PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.stock_movement import StockMovementResponse

router = APIRouter(prefix="/admin/stock", tags=["admin-stock"])


@router.get("/movements", response_model=PaginatedResponse[StockMovementResponse])
async def list_stock_movements(
    pagination: Annotated[PaginationParams, Depends()],
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> PaginatedResponse[StockMovementResponse]:
    movements, total = await StockMovementRepository(session).list_all(pagination)
    return PaginatedResponse[StockMovementResponse](
        message="Stock movements retrieved successfully",
        data=[StockMovementResponse.from_model(movement) for movement in movements],
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )


@router.get("/movements/{product_item_id}", response_model=PaginatedResponse[StockMovementResponse])
async def list_stock_movements_by_product_item(
    product_item_id: UUID,
    pagination: Annotated[PaginationParams, Depends()],
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> PaginatedResponse[StockMovementResponse]:
    movements, total = await StockMovementRepository(session).list_by_product_item(
        product_item_id,
        pagination,
    )
    return PaginatedResponse[StockMovementResponse](
        message="Stock movements by product item retrieved successfully",
        data=[StockMovementResponse.from_model(movement) for movement in movements],
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )
