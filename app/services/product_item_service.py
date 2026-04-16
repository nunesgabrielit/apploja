from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.enums import StockMovementSource, StockMovementType
from app.models.product_item import ProductItem
from app.models.user import User
from app.repositories.product_item_repository import ProductItemRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.stock_movement_repository import StockMovementRepository
from app.schemas.common import PaginationParams
from app.schemas.product_item import (
    ProductItemCreate,
    ProductItemListFilters,
    ProductItemPriceUpdate,
    ProductItemStockUpdate,
    ProductItemUpdate,
    StockOperation,
)
from app.utils.audit import AuditAction, register_audit_event


class ProductItemService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.product_item_repository = ProductItemRepository(session)
        self.product_repository = ProductRepository(session)
        self.stock_movement_repository = StockMovementRepository(session)

    async def list_active(
        self,
        filters: ProductItemListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[ProductItem], int]:
        return await self.product_item_repository.list_active(filters, pagination)

    async def get_public_by_id(self, item_id: UUID) -> ProductItem:
        item = await self.product_item_repository.get_public_by_id(item_id)
        if item is None:
            raise NotFoundError("Product item not found")
        return item

    async def create(self, payload: ProductItemCreate, actor: User) -> ProductItem:
        await self._ensure_product_exists(payload.product_id)
        await self._validate_uniqueness(payload.internal_code, payload.sku)
        self._validate_price(payload.price)

        try:
            item = await self.product_item_repository.create(
                product_id=payload.product_id,
                internal_code=payload.internal_code,
                sku=payload.sku,
                name=payload.name,
                connector_type=payload.connector_type,
                power=payload.power,
                voltage=payload.voltage,
                short_description=payload.short_description,
                price=payload.price,
                stock_current=payload.stock_current,
                stock_minimum=payload.stock_minimum,
            )
            await register_audit_event(
                self.session,
                action=AuditAction.PRODUCT_ITEM_CREATED,
                actor=actor,
                entity="product_item",
                entity_id=item.id,
                metadata={"sku": item.sku, "internal_code": item.internal_code},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Product item internal code or SKU already exists") from exc

        item = await self._get_item(item.id)
        return item

    async def update(self, item_id: UUID, payload: ProductItemUpdate, actor: User) -> ProductItem:
        item = await self._get_item(item_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "product_id" in update_data:
            await self._ensure_product_exists(update_data["product_id"])
        if "internal_code" in update_data:
            existing_internal_code = await self.product_item_repository.get_by_internal_code(
                update_data["internal_code"],
                exclude_id=item.id,
            )
            if existing_internal_code is not None:
                raise ConflictError("A product item with this internal code already exists")
        if "sku" in update_data:
            existing_sku = await self.product_item_repository.get_by_sku(
                update_data["sku"],
                exclude_id=item.id,
            )
            if existing_sku is not None:
                raise ConflictError("A product item with this SKU already exists")

        for field, value in update_data.items():
            setattr(item, field, value)

        try:
            await register_audit_event(
                self.session,
                action=AuditAction.PRODUCT_ITEM_UPDATED,
                actor=actor,
                entity="product_item",
                entity_id=item.id,
                metadata={key: str(value) for key, value in update_data.items()},
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("A product item with this internal code or SKU already exists") from exc

        item = await self._get_item(item.id)
        return item

    async def update_stock(
        self,
        item_id: UUID,
        payload: ProductItemStockUpdate,
        actor: User,
    ) -> ProductItem:
        item = await self._get_item(item_id)
        previous_stock = item.stock_current

        if payload.operation == StockOperation.SET:
            new_stock = payload.quantity
        elif payload.operation == StockOperation.INCREMENT:
            new_stock = item.stock_current + payload.quantity
        else:
            new_stock = item.stock_current - payload.quantity

        if new_stock < 0:
            raise BusinessRuleError("Stock cannot be negative")

        item.stock_current = new_stock
        quantity_delta = abs(new_stock - previous_stock)
        await self.stock_movement_repository.create(
            product_item_id=item.id,
            order_id=None,
            payment_id=None,
            movement_type=StockMovementType.MANUAL_ADJUSTMENT,
            quantity=quantity_delta,
            source=StockMovementSource.ADMIN,
            reference_id=item.id,
            performed_by_user_id=actor.id,
            previous_stock=previous_stock,
            new_stock=new_stock,
            reason=payload.reason,
        )
        await register_audit_event(
            self.session,
            action=AuditAction.PRODUCT_ITEM_STOCK_UPDATED,
            actor=actor,
            entity="product_item",
            entity_id=item.id,
            metadata={
                "operation": payload.operation.value,
                "quantity": payload.quantity,
                "reason": payload.reason,
                "previous_stock": previous_stock,
                "new_stock": new_stock,
            },
        )
        await self.session.commit()
        item = await self._get_item(item.id)
        return item

    async def update_price(
        self,
        item_id: UUID,
        payload: ProductItemPriceUpdate,
        actor: User,
    ) -> ProductItem:
        item = await self._get_item(item_id)
        self._validate_price(payload.price)

        previous_price = item.price
        item.price = payload.price
        await register_audit_event(
            self.session,
            action=AuditAction.PRODUCT_ITEM_PRICE_UPDATED,
            actor=actor,
            entity="product_item",
            entity_id=item.id,
            metadata={"previous_price": str(previous_price), "new_price": str(item.price)},
        )
        await self.session.commit()
        item = await self._get_item(item.id)
        return item

    async def deactivate(self, item_id: UUID, actor: User) -> ProductItem:
        item = await self._get_item(item_id)
        item.is_active = False
        await register_audit_event(
            self.session,
            action=AuditAction.PRODUCT_ITEM_DELETED,
            actor=actor,
            entity="product_item",
            entity_id=item.id,
            metadata={"is_active": False},
        )
        await self.session.commit()
        item = await self._get_item(item.id)
        return item

    async def _ensure_product_exists(self, product_id: UUID) -> None:
        product = await self.product_repository.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")

    async def _get_item(self, item_id: UUID) -> ProductItem:
        item = await self.product_item_repository.get_by_id(item_id)
        if item is None:
            raise NotFoundError("Product item not found")
        return item

    async def _validate_uniqueness(self, internal_code: str, sku: str) -> None:
        existing_internal_code = await self.product_item_repository.get_by_internal_code(
            internal_code
        )
        if existing_internal_code is not None:
            raise ConflictError("A product item with this internal code already exists")

        existing_sku = await self.product_item_repository.get_by_sku(sku)
        if existing_sku is not None:
            raise ConflictError("A product item with this SKU already exists")

    def _validate_price(self, price: Decimal) -> None:
        if price <= Decimal("0"):
            raise BusinessRuleError("Price must be greater than zero")
