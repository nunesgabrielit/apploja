from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.cart import Cart
from app.models.enums import (
    CartStatus,
    FulfillmentType,
    OrderStatus,
    PaymentStatus,
    StockMovementSource,
    StockMovementType,
    UserRole,
)
from app.models.order import Order
from app.models.order_status_history import OrderStatusHistory
from app.models.user import User
from app.repositories.address_repository import AddressRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.order_status_history_repository import OrderStatusHistoryRepository
from app.repositories.product_item_repository import ProductItemRepository
from app.repositories.stock_movement_repository import StockMovementRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginationParams
from app.schemas.order import AdminOrderListFilters, AssignEmployeeRequest, OrderCreateRequest
from app.schemas.shipping import ShippingCalculateRequest
from app.services.shipping_service import ShippingService
from app.utils.audit import AuditAction, register_audit_event


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.address_repository = AddressRepository(session)
        self.cart_repository = CartRepository(session)
        self.order_repository = OrderRepository(session)
        self.order_status_history_repository = OrderStatusHistoryRepository(session)
        self.product_item_repository = ProductItemRepository(session)
        self.stock_movement_repository = StockMovementRepository(session)
        self.user_repository = UserRepository(session)

    async def create_from_cart(self, user: User, payload: OrderCreateRequest) -> Order:
        self._ensure_customer(user)
        self._validate_fulfillment_type(payload.fulfillment_type)

        cart = await self.cart_repository.get_active_by_user_id(user.id)
        if cart is None:
            raise BusinessRuleError("Cannot create an order from an empty cart")
        self._ensure_cart_has_items(cart)

        address_id, shipping_price = await self._resolve_shipping(user, payload)
        subtotal = await self._validate_cart_items_and_calculate_subtotal(cart)
        discount = Decimal("0.00")
        total = subtotal + shipping_price - discount

        order = await self.order_repository.create(
            user_id=user.id,
            address_id=address_id,
            assigned_employee_id=None,
            fulfillment_type=payload.fulfillment_type,
            order_status=OrderStatus.WAITING_PAYMENT,
            payment_status=PaymentStatus.PENDING,
            subtotal=subtotal,
            shipping_price=shipping_price,
            discount=discount,
            total=total,
            notes=payload.notes,
            created_by_user_id=user.id,
            updated_by_user_id=user.id,
        )

        for cart_item in cart.items:
            total_item = cart_item.unit_price * cart_item.quantity
            await self.order_repository.create_item(
                order_id=order.id,
                product_item_id=cart_item.product_item_id,
                internal_code_snapshot=cart_item.product_item.internal_code,
                name_snapshot=cart_item.product_item.name,
                unit_price=cart_item.unit_price,
                quantity=cart_item.quantity,
                total_item=total_item,
            )

        cart.status = CartStatus.CONVERTED
        await register_audit_event(
            self.session,
            action=AuditAction.ORDER_CREATED,
            actor=user,
            entity="order",
            entity_id=order.id,
            metadata={
                "fulfillment_type": order.fulfillment_type.value,
                "subtotal": str(order.subtotal),
                "shipping_price": str(order.shipping_price),
                "total": str(order.total),
            },
        )
        await self.session.commit()

        created_order = await self._get_order(order.id)
        return created_order

    async def list_my_orders(
        self,
        user: User,
        pagination: PaginationParams,
    ) -> tuple[list[Order], int]:
        self._ensure_customer(user)
        return await self.order_repository.list_by_user(user.id, pagination)

    async def get_my_order(self, user: User, order_id: UUID) -> Order:
        self._ensure_customer(user)
        order = await self.order_repository.get_by_user_and_id(user.id, order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    async def list_admin_orders(
        self,
        filters: AdminOrderListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[Order], int]:
        return await self.order_repository.list_admin(filters, pagination)

    async def get_admin_order(self, order_id: UUID) -> Order:
        return await self._get_order(order_id)

    async def assign_employee(
        self,
        order_id: UUID,
        payload: AssignEmployeeRequest,
        actor: User,
    ) -> Order:
        order = await self._get_order(order_id)
        assigned_user = await self.user_repository.get_by_id(payload.assigned_employee_id)
        if assigned_user is None:
            raise NotFoundError("Assigned employee not found")
        if assigned_user.role not in {UserRole.ADMIN, UserRole.EMPLOYEE}:
            raise BusinessRuleError("Assigned user must have admin or employee role")
        if not assigned_user.is_active:
            raise BusinessRuleError("Assigned user must be active")

        order.assigned_employee_id = assigned_user.id
        order.updated_by_user_id = actor.id
        await register_audit_event(
            self.session,
            action=AuditAction.ORDER_ASSIGNED_EMPLOYEE,
            actor=actor,
            entity="order",
            entity_id=order.id,
            metadata={"assigned_employee_id": str(assigned_user.id)},
        )
        await self.session.commit()

        return await self._get_order(order.id)

    async def cancel_order(
        self,
        order_id: UUID,
        actor: User,
        *,
        return_to_stock: bool = True,
    ) -> Order:
        if actor.role != UserRole.ADMIN:
            raise BusinessRuleError("Only admins can cancel orders")

        order = await self._get_order(order_id)
        if order.order_status == OrderStatus.CANCELLED:
            raise BusinessRuleError("Order is already cancelled")

        previous_status = order.order_status
        order.order_status = OrderStatus.CANCELLED
        order.updated_by_user_id = actor.id

        if order.payment_status == PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.CANCELLED

        if return_to_stock and order.payment_status == PaymentStatus.APPROVED:
            for order_item in order.items:
                product_item = await self.product_item_repository.get_by_id(order_item.product_item_id)
                if product_item is None:
                    raise NotFoundError("Product item not found")

                previous_stock = product_item.stock_current
                product_item.stock_current = previous_stock + order_item.quantity
                await self.stock_movement_repository.create(
                    product_item_id=product_item.id,
                    order_id=order.id,
                    payment_id=None,
                    movement_type=StockMovementType.RETURN,
                    quantity=order_item.quantity,
                    source=StockMovementSource.ADMIN,
                    reference_id=order.id,
                    performed_by_user_id=actor.id,
                    previous_stock=previous_stock,
                    new_stock=product_item.stock_current,
                    reason=f"Order {order.id} cancelled with stock return",
                )

        await self._register_status_change(
            order=order,
            previous_status=previous_status,
            new_status=OrderStatus.CANCELLED,
            actor=actor,
        )
        await register_audit_event(
            self.session,
            action=AuditAction.ORDER_CANCELLED,
            actor=actor,
            entity="order",
            entity_id=order.id,
            metadata={
                "previous_status": previous_status.value,
                "new_status": OrderStatus.CANCELLED.value,
                "payment_status": order.payment_status.value,
                "return_to_stock": return_to_stock,
            },
        )
        await self.session.commit()
        return await self._get_order(order.id)

    async def list_order_status_history(self, order_id: UUID) -> list[OrderStatusHistory]:
        await self._get_order(order_id)
        return await self.order_status_history_repository.list_by_order(order_id)

    async def list_employee_performance(self) -> list[dict]:
        return await self.order_repository.list_employee_performance()

    async def _resolve_shipping(
        self,
        user: User,
        payload: OrderCreateRequest,
    ) -> tuple[UUID | None, Decimal]:
        if payload.fulfillment_type == FulfillmentType.PICKUP:
            return None, Decimal("0.00")

        if payload.address_id is None:
            raise BusinessRuleError("address_id is required for delivery orders")

        address = await self.address_repository.get_by_user_and_id(user.id, payload.address_id)
        if address is None or not address.is_active:
            raise NotFoundError("Address not found")

        shipping_result = await ShippingService(self.session).calculate(
            ShippingCalculateRequest(
                zip_code=address.zip_code,
                address_id=address.id,
                fulfillment_type=FulfillmentType.DELIVERY,
            )
        )
        return address.id, shipping_result.shipping_price

    async def _validate_cart_items_and_calculate_subtotal(self, cart: Cart) -> Decimal:
        subtotal = Decimal("0.00")

        for cart_item in cart.items:
            product_item = await self.product_item_repository.get_by_id(cart_item.product_item_id)
            if product_item is None:
                raise NotFoundError("Product item not found")
            if not product_item.is_active or not product_item.product.is_active:
                raise BusinessRuleError("Cart contains unavailable items")
            if product_item.product.category is not None and not product_item.product.category.is_active:
                raise BusinessRuleError("Cart contains unavailable items")
            if product_item.stock_current < cart_item.quantity:
                raise BusinessRuleError("Cart contains items with insufficient stock")

            subtotal += cart_item.unit_price * cart_item.quantity

        return subtotal

    async def _get_order(self, order_id: UUID) -> Order:
        order = await self.order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    async def _register_status_change(
        self,
        *,
        order: Order,
        previous_status: OrderStatus | None,
        new_status: OrderStatus,
        actor: User | None,
    ) -> None:
        if previous_status == new_status:
            return
        await self.order_status_history_repository.create(
            order_id=order.id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by_user_id=actor.id if actor is not None else None,
        )
        await register_audit_event(
            self.session,
            action=AuditAction.ORDER_STATUS_CHANGED,
            actor=actor,
            entity="order",
            entity_id=order.id,
            metadata={
                "previous_status": previous_status.value if previous_status is not None else None,
                "new_status": new_status.value,
            },
        )

    def _ensure_cart_has_items(self, cart: Cart) -> None:
        if not cart.items:
            raise BusinessRuleError("Cannot create an order from an empty cart")

    def _ensure_customer(self, user: User) -> None:
        if user.role != UserRole.CUSTOMER:
            raise BusinessRuleError("Only customers can create or view personal orders")

    def _validate_fulfillment_type(self, fulfillment_type: FulfillmentType) -> None:
        if fulfillment_type not in {FulfillmentType.PICKUP, FulfillmentType.DELIVERY}:
            raise BusinessRuleError("Unsupported fulfillment type for orders")
