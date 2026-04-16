from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_loader_criteria

from app.models.category import Category
from app.models.product import Product
from app.models.product_item import ProductItem
from app.schemas.common import PaginationParams
from app.schemas.product import ProductListFilters


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: UUID) -> Product | None:
        statement = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.category),
                selectinload(Product.items),
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_public_by_id(self, product_id: UUID) -> Product | None:
        statement = (
            select(Product)
            .join(Product.category)
            .where(
                Product.id == product_id,
                Product.is_active.is_(True),
                Category.is_active.is_(True),
            )
            .options(
                selectinload(Product.category),
                selectinload(Product.items),
                with_loader_criteria(ProductItem, ProductItem.is_active.is_(True), include_aliases=True),
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_active(
        self,
        filters: ProductListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[Product], int]:
        conditions = [
            Product.is_active.is_(True),
            Category.is_active.is_(True),
        ]

        if filters.category_id is not None:
            conditions.append(Product.category_id == filters.category_id)
        if filters.brand is not None:
            conditions.append(func.lower(Product.brand) == filters.brand.strip().lower())
        if filters.search is not None:
            conditions.append(Product.name_base.ilike(f"%{filters.search.strip()}%"))

        total_statement = select(func.count(Product.id)).join(Product.category).where(*conditions)
        total = await self.session.scalar(total_statement)

        statement = (
            select(Product)
            .join(Product.category)
            .where(*conditions)
            .options(
                selectinload(Product.category),
                selectinload(Product.items),
                with_loader_criteria(ProductItem, ProductItem.is_active.is_(True), include_aliases=True),
            )
            .order_by(Product.name_base.asc(), Product.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all()), int(total or 0)

    async def create(
        self,
        *,
        category_id: UUID,
        name_base: str,
        brand: str | None,
        description: str | None,
        image_url: str | None,
    ) -> Product:
        product = Product(
            category_id=category_id,
            name_base=name_base.strip(),
            brand=brand,
            description=description,
            image_url=image_url,
        )
        self.session.add(product)
        await self.session.flush()
        return product
