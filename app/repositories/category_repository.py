from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.common import PaginationParams


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, category_id: UUID) -> Category | None:
        return await self.session.get(Category, category_id)

    async def get_by_name(self, name: str, *, exclude_id: UUID | None = None) -> Category | None:
        statement = select(Category).where(func.lower(Category.name) == name.strip().lower())
        if exclude_id is not None:
            statement = statement.where(Category.id != exclude_id)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_active(self, pagination: PaginationParams) -> tuple[list[Category], int]:
        filters = (Category.is_active.is_(True),)

        total_statement = select(func.count(Category.id)).where(*filters)
        total = await self.session.scalar(total_statement)

        statement = (
            select(Category)
            .where(*filters)
            .order_by(Category.name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all()), int(total or 0)

    async def create(self, *, name: str, description: str | None) -> Category:
        category = Category(name=name.strip(), description=description)
        self.session.add(category)
        await self.session.flush()
        return category
