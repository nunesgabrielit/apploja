from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.common import PaginationParams
from app.utils.audit import AuditAction, log_admin_audit


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.category_repository = CategoryRepository(session)

    async def list_active(self, pagination: PaginationParams) -> tuple[list[Category], int]:
        return await self.category_repository.list_active(pagination)

    async def create(self, payload: CategoryCreate, actor: User) -> Category:
        existing_category = await self.category_repository.get_by_name(payload.name)
        if existing_category is not None:
            raise ConflictError("A category with this name already exists")

        try:
            category = await self.category_repository.create(
                name=payload.name,
                description=payload.description,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("A category with this name already exists") from exc

        await self.session.refresh(category)
        log_admin_audit(
            action=AuditAction.CATEGORY_CREATED,
            actor=actor,
            entity="category",
            entity_id=category.id,
            details={"name": category.name},
        )
        return category

    async def update(self, category_id: UUID, payload: CategoryUpdate, actor: User) -> Category:
        category = await self._get_category(category_id)

        if payload.name is not None:
            existing_category = await self.category_repository.get_by_name(
                payload.name,
                exclude_id=category.id,
            )
            if existing_category is not None:
                raise ConflictError("A category with this name already exists")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("A category with this name already exists") from exc

        await self.session.refresh(category)
        log_admin_audit(
            action=AuditAction.CATEGORY_UPDATED,
            actor=actor,
            entity="category",
            entity_id=category.id,
            details=update_data,
        )
        return category

    async def deactivate(self, category_id: UUID, actor: User) -> Category:
        category = await self._get_category(category_id)
        category.is_active = False
        await self.session.commit()
        await self.session.refresh(category)

        log_admin_audit(
            action=AuditAction.CATEGORY_DELETED,
            actor=actor,
            entity="category",
            entity_id=category.id,
            details={"is_active": False},
        )
        return category

    async def _get_category(self, category_id: UUID) -> Category:
        category = await self.category_repository.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        return category
