from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import OrderStatus, PaymentStatus, UserRole
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.schemas.common import PaginationParams
from app.schemas.order import AdminOrderListFilters


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _detail_load_options(self) -> tuple:
        return (
            selectinload(Order.items),
            selectinload(Order.address),
            selectinload(Order.payments),
            selectinload(Order.user),
            selectinload(Order.assigned_employee),
        )

    async def get_by_id(self, order_id: UUID) -> Order | None:
        statement = select(Order).where(Order.id == order_id).options(*self._detail_load_options())
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_user_and_id(self, user_id: UUID, order_id: UUID) -> Order | None:
        statement = (
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(*self._detail_load_options())
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        pagination: PaginationParams,
    ) -> tuple[list[Order], int]:
        conditions = [Order.user_id == user_id]

        total_statement = select(func.count(Order.id)).where(*conditions)
        total = await self.session.scalar(total_statement)

        statement = (
            select(Order)
            .where(*conditions)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all()), int(total or 0)

    async def list_admin(
        self,
        filters: AdminOrderListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[Order], int]:
        conditions = []
        if filters.order_status is not None:
            conditions.append(Order.order_status == filters.order_status)
        if filters.payment_status is not None:
            conditions.append(Order.payment_status == filters.payment_status)
        if filters.fulfillment_type is not None:
            conditions.append(Order.fulfillment_type == filters.fulfillment_type)
        if filters.user_id is not None:
            conditions.append(Order.user_id == filters.user_id)
        if filters.assigned_employee_id is not None:
            conditions.append(Order.assigned_employee_id == filters.assigned_employee_id)

        total_statement = select(func.count(Order.id)).where(*conditions)
        total = await self.session.scalar(total_statement)

        statement = (
            select(Order)
            .where(*conditions)
            .options(
                selectinload(Order.items),
                selectinload(Order.assigned_employee),
                selectinload(Order.user),
            )
            .order_by(Order.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all()), int(total or 0)

    async def list_employee_performance(self) -> list[dict]:
        finalized_statuses = (OrderStatus.DELIVERED, OrderStatus.CANCELLED)
        statement = (
            select(
                User.id.label("employee_id"),
                User.name.label("employee_name"),
                User.email.label("employee_email"),
                func.count(Order.id).label("assigned_orders"),
                func.count(
                    case(
                        (Order.order_status != OrderStatus.WAITING_PAYMENT, 1),
                        else_=None,
                    )
                ).label("processed_orders"),
                func.count(
                    case(
                        (Order.order_status.in_(finalized_statuses), 1),
                        else_=None,
                    )
                ).label("completed_orders"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                and_(
                                    Order.payment_status == PaymentStatus.APPROVED,
                                    Order.order_status != OrderStatus.CANCELLED,
                                ),
                                Order.total,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("total_sold"),
            )
            .select_from(User)
            .outerjoin(Order, Order.assigned_employee_id == User.id)
            .where(User.role.in_([UserRole.ADMIN, UserRole.EMPLOYEE]), User.is_active.is_(True))
            .group_by(User.id, User.name, User.email)
            .order_by(User.name.asc())
        )
        result = await self.session.execute(statement)
        return [dict(row._mapping) for row in result]

    async def create(
        self,
        *,
        user_id: UUID,
        address_id: UUID | None,
        assigned_employee_id: UUID | None,
        fulfillment_type,
        order_status,
        payment_status,
        subtotal: Decimal,
        shipping_price: Decimal,
        discount: Decimal,
        total: Decimal,
        notes: str | None,
        created_by_user_id: UUID | None,
        updated_by_user_id: UUID | None,
    ) -> Order:
        order = Order(
            user_id=user_id,
            address_id=address_id,
            assigned_employee_id=assigned_employee_id,
            fulfillment_type=fulfillment_type,
            order_status=order_status,
            payment_status=payment_status,
            subtotal=subtotal,
            shipping_price=shipping_price,
            discount=discount,
            total=total,
            notes=notes,
            created_by_user_id=created_by_user_id,
            updated_by_user_id=updated_by_user_id,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def create_item(
        self,
        *,
        order_id: UUID,
        product_item_id: UUID,
        internal_code_snapshot: str,
        name_snapshot: str,
        unit_price: Decimal,
        quantity: int,
        total_item: Decimal,
    ) -> OrderItem:
        order_item = OrderItem(
            order_id=order_id,
            product_item_id=product_item_id,
            internal_code_snapshot=internal_code_snapshot,
            name_snapshot=name_snapshot,
            unit_price=unit_price,
            quantity=quantity,
            total_item=total_item,
        )
        self.session.add(order_item)
        await self.session.flush()
        return order_item
