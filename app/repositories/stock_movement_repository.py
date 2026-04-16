from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import StockMovementSource, StockMovementType
from app.models.stock_movement import StockMovement
from app.schemas.common import PaginationParams


class StockMovementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        product_item_id: UUID,
        order_id: UUID | None,
        payment_id: UUID | None,
        movement_type: StockMovementType,
        quantity: int,
        source: StockMovementSource,
        reference_id: UUID | None,
        performed_by_user_id: UUID | None,
        previous_stock: int,
        new_stock: int,
        reason: str | None,
    ) -> StockMovement:
        movement = StockMovement(
            product_item_id=product_item_id,
            order_id=order_id,
            payment_id=payment_id,
            movement_type=movement_type,
            quantity=quantity,
            source=source,
            reference_id=reference_id,
            performed_by_user_id=performed_by_user_id,
            previous_stock=previous_stock,
            new_stock=new_stock,
            reason=reason,
        )
        self.session.add(movement)
        await self.session.flush()
        return movement

    async def list_all(self, pagination: PaginationParams) -> tuple[list[StockMovement], int]:
        total = await self.session.scalar(select(func.count(StockMovement.id)))
        statement = (
            select(StockMovement)
            .options(selectinload(StockMovement.product_item), selectinload(StockMovement.performed_by_user))
            .order_by(StockMovement.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all()), int(total or 0)

    async def list_by_product_item(
        self,
        product_item_id: UUID,
        pagination: PaginationParams,
    ) -> tuple[list[StockMovement], int]:
        conditions = [StockMovement.product_item_id == product_item_id]
        total = await self.session.scalar(select(func.count(StockMovement.id)).where(*conditions))
        statement = (
            select(StockMovement)
            .where(*conditions)
            .options(selectinload(StockMovement.product_item), selectinload(StockMovement.performed_by_user))
            .order_by(StockMovement.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all()), int(total or 0)
