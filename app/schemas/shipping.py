from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.enums import FulfillmentType

ZipCodeInputStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=32),
]
RuleNameStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=255),
]
OptionalEstimatedText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]
NonNegativePriceDecimal = Annotated[
    Decimal,
    Field(ge=Decimal("0"), max_digits=10, decimal_places=2),
]


class ShippingRuleCreate(BaseModel):
    zip_code_start: ZipCodeInputStr
    zip_code_end: ZipCodeInputStr
    rule_name: RuleNameStr
    shipping_price: NonNegativePriceDecimal
    estimated_time_text: OptionalEstimatedText | None = None


class ShippingRuleUpdate(BaseModel):
    zip_code_start: ZipCodeInputStr | None = None
    zip_code_end: ZipCodeInputStr | None = None
    rule_name: RuleNameStr | None = None
    shipping_price: NonNegativePriceDecimal | None = None
    estimated_time_text: OptionalEstimatedText | None = None
    is_active: bool | None = None


class ShippingRuleListFilters(BaseModel):
    is_active: bool | None = None


class ShippingRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    zip_code_start: str
    zip_code_end: str
    rule_name: str
    shipping_price: Decimal
    estimated_time_text: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, rule: object) -> "ShippingRuleResponse":
        return cls.model_validate(rule)


class ShippingStoreConfigUpsert(BaseModel):
    store_name: RuleNameStr = "WM Distribuidora"
    zip_code: ZipCodeInputStr
    street: RuleNameStr
    number: RuleNameStr
    district: RuleNameStr
    city: RuleNameStr
    state: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=2)]
    complement: OptionalEstimatedText | None = None


class ShippingStoreConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    store_name: str
    zip_code: str
    street: str
    number: str
    district: str
    city: str
    state: str
    complement: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, config: object) -> "ShippingStoreConfigResponse":
        return cls.model_validate(config)


class ShippingDistanceRuleCreate(BaseModel):
    rule_name: RuleNameStr
    max_distance_km: Annotated[Decimal, Field(gt=Decimal("0"), max_digits=6, decimal_places=2)]
    shipping_price: NonNegativePriceDecimal
    estimated_time_text: OptionalEstimatedText | None = None
    sort_order: int = Field(default=0, ge=0)


class ShippingDistanceRuleUpdate(BaseModel):
    rule_name: RuleNameStr | None = None
    max_distance_km: Annotated[Decimal, Field(gt=Decimal("0"), max_digits=6, decimal_places=2)] | None = None
    shipping_price: NonNegativePriceDecimal | None = None
    estimated_time_text: OptionalEstimatedText | None = None
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ShippingDistanceRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_name: str
    max_distance_km: Decimal
    shipping_price: Decimal
    estimated_time_text: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, rule: object) -> "ShippingDistanceRuleResponse":
        return cls.model_validate(rule)


class ShippingCalculateRequest(BaseModel):
    zip_code: ZipCodeInputStr | None = None
    address_id: UUID | None = None
    fulfillment_type: FulfillmentType


class ShippingCalculateResponse(BaseModel):
    zip_code: str | None
    zip_code_normalized: str | None
    fulfillment_type: FulfillmentType
    shipping_price: Decimal
    estimated_time_text: str | None
    rule_name: str
    covered: bool
    calculation_mode: Literal["pickup", "distance", "zip_code"]
    distance_km: Decimal | None = None
