from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.category import Category
from app.models.product import Product
from app.models.product_item import ProductItem
from app.schemas.common import PaginationParams
from app.schemas.product_item import ProductItemListFilters


class ProductItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, item_id: UUID) -> ProductItem | None:
        statement = (
            select(ProductItem)
            .where(ProductItem.id == item_id)
            .options(joinedload(ProductItem.product).joinedload(Product.category))
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_public_by_id(self, item_id: UUID) -> ProductItem | None:
        statement = (
            select(ProductItem)
            .join(ProductItem.product)
            .join(Product.category)
            .where(
                ProductItem.id == item_id,
                ProductItem.is_active.is_(True),
                Product.is_active.is_(True),
                Category.is_active.is_(True),
            )
            .options(joinedload(ProductItem.product).joinedload(Product.category))
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_internal_code(
        self,
        internal_code: str,
        *,
        exclude_id: UUID | None = None,
    ) -> ProductItem | None:
        statement = select(ProductItem).where(
            func.lower(ProductItem.internal_code) == internal_code.strip().lower()
        )
        if exclude_id is not None:
            statement = statement.where(ProductItem.id != exclude_id)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str, *, exclude_id: UUID | None = None) -> ProductItem | None:
        statement = select(ProductItem).where(func.lower(ProductItem.sku) == sku.strip().lower())
        if exclude_id is not None:
            statement = statement.where(ProductItem.id != exclude_id)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        filters: ProductItemListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[ProductItem], int]:
        conditions = [
            ProductItem.is_active.is_(True),
            Product.is_active.is_(True),
            Category.is_active.is_(True),
        ]

        if filters.product_id is not None:
            conditions.append(ProductItem.product_id == filters.product_id)
        if filters.category_id is not None:
            conditions.append(Product.category_id == filters.category_id)
        if filters.brand is not None:
            conditions.append(func.lower(Product.brand) == filters.brand.strip().lower())
        if filters.internal_code is not None:
            conditions.append(
                func.lower(ProductItem.internal_code) == filters.internal_code.strip().lower()
            )
        if filters.sku is not None:
            conditions.append(func.lower(ProductItem.sku) == filters.sku.strip().lower())
        if filters.search is not None:
            conditions.append(ProductItem.name.ilike(f"%{filters.search.strip()}%"))
        if filters.low_stock is True:
            conditions.append(ProductItem.stock_current <= ProductItem.stock_minimum)
        elif filters.low_stock is False:
            conditions.append(ProductItem.stock_current > ProductItem.stock_minimum)

        total_statement = (
            select(func.count(ProductItem.id))
            .join(ProductItem.product)
            .join(Product.category)
            .where(*conditions)
        )
        total = await self.session.scalar(total_statement)

        statement = (
            select(ProductItem)
            .join(ProductItem.product)
            .join(Product.category)
            .where(*conditions)
            .options(joinedload(ProductItem.product).joinedload(Product.category))
            .order_by(ProductItem.name.asc(), ProductItem.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all()), int(total or 0)

    async def create(
        self,
        *,
        product_id: UUID,
        internal_code: str,
        sku: str,
        name: str,
        connector_type: str | None,
        power: str | None,
        voltage: str | None,
        short_description: str | None,
        price: Decimal,
        stock_current: int,
        stock_minimum: int,
    ) -> ProductItem:
        item = ProductItem(
            product_id=product_id,
            internal_code=internal_code.strip(),
            sku=sku.strip(),
            name=name.strip(),
            connector_type=connector_type,
            power=power,
            voltage=voltage,
            short_description=short_description,
            price=price,
            stock_current=stock_current,
            stock_minimum=stock_minimum,
        )
        self.session.add(item)
        await self.session.flush()
        return item
