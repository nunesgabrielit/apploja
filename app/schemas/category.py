from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

CategoryNameStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=120),
]
DescriptionStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=1000),
]


class CategoryCreate(BaseModel):
    name: CategoryNameStr
    description: DescriptionStr | None = None


class CategoryUpdate(BaseModel):
    name: CategoryNameStr | None = None
    description: DescriptionStr | None = None
    is_active: bool | None = None


class CategoryListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None

    @classmethod
    def from_model(cls, category: object) -> "CategoryListItem":
        return cls.model_validate(category)


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str

    @classmethod
    def from_model(cls, category: object) -> "CategorySummary":
        return cls.model_validate(category)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, category: object) -> "CategoryRead":
        return cls.model_validate(category)
