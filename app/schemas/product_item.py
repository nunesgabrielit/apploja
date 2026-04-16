from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

PriceDecimal = Annotated[Decimal, Field(gt=Decimal("0"), max_digits=10, decimal_places=2)]
NonNegativeInt = Annotated[int, Field(ge=0)]
CodeStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
OptionalShortText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
OptionalDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]


class StockOperation(str, Enum):
    SET = "set"
    INCREMENT = "increment"
    DECREMENT = "decrement"


class ProductItemCreate(BaseModel):
    product_id: UUID
    internal_code: CodeStr
    sku: CodeStr
    name: NameStr
    connector_type: OptionalShortText | None = None
    power: OptionalShortText | None = None
    voltage: OptionalShortText | None = None
    short_description: OptionalDescription | None = None
    price: PriceDecimal
    stock_current: NonNegativeInt = 0
    stock_minimum: NonNegativeInt = 5


class ProductItemUpdate(BaseModel):
    product_id: UUID | None = None
    internal_code: CodeStr | None = None
    sku: CodeStr | None = None
    name: NameStr | None = None
    connector_type: OptionalShortText | None = None
    power: OptionalShortText | None = None
    voltage: OptionalShortText | None = None
    short_description: OptionalDescription | None = None
    stock_minimum: NonNegativeInt | None = None
    is_active: bool | None = None


class ProductItemPriceUpdate(BaseModel):
    price: PriceDecimal


class ProductItemStockUpdate(BaseModel):
    quantity: NonNegativeInt
    operation: StockOperation
    reason: OptionalDescription | None = None


class ProductItemListFilters(BaseModel):
    product_id: UUID | None = None
    category_id: UUID | None = None
    brand: str | None = Field(default=None, min_length=1, max_length=120)
    internal_code: str | None = Field(default=None, min_length=1, max_length=100)
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    search: str | None = Field(default=None, min_length=1, max_length=255)
    low_stock: bool | None = None


class ProductItemSummary(BaseModel):
    id: UUID
    internal_code: str
    sku: str
    name: str
    price: Decimal
    stock_current: int
    stock_minimum: int
    low_stock: bool

    @classmethod
    def from_model(cls, item: object) -> "ProductItemSummary":
        return cls(
            id=item.id,
            internal_code=item.internal_code,
            sku=item.sku,
            name=item.name,
            price=item.price,
            stock_current=item.stock_current,
            stock_minimum=item.stock_minimum,
            low_stock=item.stock_current <= item.stock_minimum,
        )


class ProductItemProductSummary(BaseModel):
    id: UUID
    category_id: UUID
    name_base: str
    brand: str | None


class ProductItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    internal_code: str
    sku: str
    name: str
    connector_type: str | None
    power: str | None
    voltage: str | None
    short_description: str | None
    price: Decimal
    stock_current: int
    stock_minimum: int
    low_stock: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    product: ProductItemProductSummary

    @classmethod
    def from_model(cls, item: object) -> "ProductItemRead":
        return cls(
            id=item.id,
            product_id=item.product_id,
            internal_code=item.internal_code,
            sku=item.sku,
            name=item.name,
            connector_type=item.connector_type,
            power=item.power,
            voltage=item.voltage,
            short_description=item.short_description,
            price=item.price,
            stock_current=item.stock_current,
            stock_minimum=item.stock_minimum,
            low_stock=item.stock_current <= item.stock_minimum,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
            product=ProductItemProductSummary(
                id=item.product.id,
                category_id=item.product.category_id,
                name_base=item.product.name_base,
                brand=item.product.brand,
            ),
        )


class ProductItemListItem(BaseModel):
    id: UUID
    product_id: UUID
    category_id: UUID
    brand: str | None
    internal_code: str
    sku: str
    name: str
    product_name_base: str
    price: Decimal
    stock_current: int
    stock_minimum: int
    low_stock: bool

    @classmethod
    def from_model(cls, item: object) -> "ProductItemListItem":
        return cls(
            id=item.id,
            product_id=item.product_id,
            category_id=item.product.category_id,
            brand=item.product.brand,
            internal_code=item.internal_code,
            sku=item.sku,
            name=item.name,
            product_name_base=item.product.name_base,
            price=item.price,
            stock_current=item.stock_current,
            stock_minimum=item.stock_minimum,
            low_stock=item.stock_current <= item.stock_minimum,
        )
