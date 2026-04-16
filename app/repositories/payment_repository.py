from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.enums import PaymentMethod, PaymentProvider, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _detail_load_options(self) -> tuple:
        return (
            selectinload(Payment.order)
            .selectinload(Order.items)
            .selectinload(OrderItem.product_item),
        )

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        statement = select(Payment).where(Payment.id == payment_id).options(*self._detail_load_options())
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> Payment | None:
        statement = (
            select(Payment)
            .where(Payment.external_id == external_id)
            .options(*self._detail_load_options())
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_latest_open_by_order_id(self, order_id: UUID) -> Payment | None:
        statement = (
            select(Payment)
            .where(
                Payment.order_id == order_id,
                Payment.status.in_(
                    [
                        PaymentStatus.PENDING,
                        PaymentStatus.AUTHORIZED,
                        PaymentStatus.APPROVED,
                    ]
                ),
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        order_id: UUID,
        provider: PaymentProvider,
        method: PaymentMethod,
        status: PaymentStatus,
        amount: Decimal,
        external_id: str | None = None,
        qr_code: str | None = None,
        copy_paste_code: str | None = None,
        provider_payload: dict[str, Any] | None = None,
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            provider=provider,
            method=method,
            status=status,
            amount=amount,
            external_id=external_id,
            qr_code=qr_code,
            copy_paste_code=copy_paste_code,
            provider_payload=provider_payload,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment
