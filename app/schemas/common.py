from __future__ import annotations

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def create(cls, *, page: int, page_size: int, total: int) -> "PaginationMeta":
        total_pages = math.ceil(total / page_size) if total else 0
        return cls(page=page, page_size=page_size, total=total, total_pages=total_pages)


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: list[T]
    pagination: PaginationMeta
