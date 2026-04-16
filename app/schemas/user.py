from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, field_validator

from app.models.enums import UserRole

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
PhoneStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=8, max_length=20)]
PasswordStr = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UserBase(BaseModel):
    name: NameStr
    email: EmailStr
    phone: PhoneStr | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserRegister(UserBase):
    password: PasswordStr


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
