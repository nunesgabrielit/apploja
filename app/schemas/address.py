from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
ZipCodeStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=8, max_length=16)]
StateStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=2)]


class AddressCreate(BaseModel):
    recipient_name: ShortText
    zip_code: ZipCodeStr
    street: ShortText
    number: ShortText
    district: ShortText
    city: ShortText
    state: StateStr
    complement: ShortText | None = None


class AddressUpdate(BaseModel):
    recipient_name: ShortText | None = None
    zip_code: ZipCodeStr | None = None
    street: ShortText | None = None
    number: ShortText | None = None
    district: ShortText | None = None
    city: ShortText | None = None
    state: StateStr | None = None
    complement: ShortText | None = None
    is_active: bool | None = None


class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    recipient_name: str
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
    def from_model(cls, address: object) -> "AddressRead":
        return cls.model_validate(address)
