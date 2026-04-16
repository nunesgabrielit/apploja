from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.category import CategorySummary
from app.schemas.product_item import ProductItemSummary

ProductNameStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=255),
]
BrandStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]
DescriptionStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]
ImageUrlStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]


class ProductCreate(BaseModel):
    category_id: UUID
    name_base: ProductNameStr
    brand: BrandStr | None = None
    description: DescriptionStr | None = None
    image_url: ImageUrlStr | None = None


class ProductUpdate(BaseModel):
    category_id: UUID | None = None
    name_base: ProductNameStr | None = None
    brand: BrandStr | None = None
    description: DescriptionStr | None = None
    image_url: ImageUrlStr | None = None
    is_active: bool | None = None


class ProductListFilters(BaseModel):
    category_id: UUID | None = None
    brand: str | None = Field(default=None, min_length=1, max_length=120)
    search: str | None = Field(default=None, min_length=1, max_length=255)


class ProductListItem(BaseModel):
    id: UUID
    category: CategorySummary
    name_base: str
    brand: str | None
    description: str | None
    image_url: str | None
    items: list[ProductItemSummary]

    @classmethod
    def from_model(cls, product: object) -> "ProductListItem":
        active_items = [item for item in product.items if item.is_active]
        return cls(
            id=product.id,
            category=CategorySummary.from_model(product.category),
            name_base=product.name_base,
            brand=product.brand,
            description=product.description,
            image_url=product.image_url,
            items=[ProductItemSummary.from_model(item) for item in active_items],
        )


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: CategorySummary
    name_base: str
    brand: str | None
    description: str | None
    image_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: list[ProductItemSummary]

    @classmethod
    def from_model(cls, product: object) -> "ProductRead":
        active_items = [item for item in product.items if item.is_active]
        return cls(
            id=product.id,
            category=CategorySummary.from_model(product.category),
            name_base=product.name_base,
            brand=product.brand,
            description=product.description,
            image_url=product.image_url,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            items=[ProductItemSummary.from_model(item) for item in active_items],
        )
