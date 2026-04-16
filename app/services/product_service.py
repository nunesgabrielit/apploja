from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.common import PaginationParams
from app.schemas.product import ProductCreate, ProductListFilters, ProductUpdate
from app.utils.audit import AuditAction, register_audit_event


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.category_repository = CategoryRepository(session)
        self.product_repository = ProductRepository(session)

    async def list_active(
        self,
        filters: ProductListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[Product], int]:
        return await self.product_repository.list_active(filters, pagination)

    async def get_public_by_id(self, product_id: UUID) -> Product:
        product = await self.product_repository.get_public_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def create(self, payload: ProductCreate, actor: User) -> Product:
        await self._ensure_category_exists(payload.category_id)

        product = await self.product_repository.create(
            category_id=payload.category_id,
            name_base=payload.name_base,
            brand=payload.brand,
            description=payload.description,
            image_url=payload.image_url,
        )
        await register_audit_event(
            self.session,
            action=AuditAction.PRODUCT_CREATED,
            actor=actor,
            entity="product",
            entity_id=product.id,
            metadata={"name_base": product.name_base, "category_id": str(product.category_id)},
        )
        await self.session.commit()
        product = await self._get_product(product.id)
        return product

    async def update(self, product_id: UUID, payload: ProductUpdate, actor: User) -> Product:
        product = await self._get_product(product_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "category_id" in update_data:
            await self._ensure_category_exists(update_data["category_id"])

        for field, value in update_data.items():
            setattr(product, field, value)

        await register_audit_event(
            self.session,
            action=AuditAction.PRODUCT_UPDATED,
            actor=actor,
            entity="product",
            entity_id=product.id,
            metadata={key: str(value) for key, value in update_data.items()},
        )
        await self.session.commit()
        product = await self._get_product(product.id)
        return product

    async def deactivate(self, product_id: UUID, actor: User) -> Product:
        product = await self._get_product(product_id)
        product.is_active = False
        await register_audit_event(
            self.session,
            action=AuditAction.PRODUCT_DELETED,
            actor=actor,
            entity="product",
            entity_id=product.id,
            metadata={"is_active": False},
        )
        await self.session.commit()
        product = await self._get_product(product.id)
        return product

    async def _ensure_category_exists(self, category_id: UUID) -> None:
        category = await self.category_repository.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found")

    async def _get_product(self, product_id: UUID) -> Product:
        product = await self.product_repository.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product
