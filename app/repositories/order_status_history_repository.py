from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import OrderStatus
from app.models.order_status_history import OrderStatusHistory


class OrderStatusHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        order_id: UUID,
        previous_status: OrderStatus | None,
        new_status: OrderStatus,
        changed_by_user_id: UUID | None,
    ) -> OrderStatusHistory:
        history = OrderStatusHistory(
            order_id=order_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by_user_id=changed_by_user_id,
        )
        self.session.add(history)
        await self.session.flush()
        return history

    async def list_by_order(self, order_id: UUID) -> list[OrderStatusHistory]:
        statement = (
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order_id)
            .options(selectinload(OrderStatusHistory.changed_by_user))
            .order_by(OrderStatusHistory.created_at.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
