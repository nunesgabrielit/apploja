from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.cart import Cart
    from app.models.order import Order


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=UserRole.CUSTOMER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    carts: Mapped[list[Cart]] = relationship(
        back_populates="user",
        lazy="selectin",
    )
    addresses: Mapped[list[Address]] = relationship(
        back_populates="user",
        lazy="selectin",
    )
    orders: Mapped[list[Order]] = relationship(
        back_populates="user",
        foreign_keys="Order.user_id",
        lazy="selectin",
    )
    assigned_orders: Mapped[list[Order]] = relationship(
        back_populates="assigned_employee",
        foreign_keys="Order.assigned_employee_id",
        lazy="selectin",
    )
    created_orders: Mapped[list[Order]] = relationship(
        back_populates="created_by_user",
        foreign_keys="Order.created_by_user_id",
        lazy="selectin",
    )
    updated_orders: Mapped[list[Order]] = relationship(
        back_populates="updated_by_user",
        foreign_keys="Order.updated_by_user_id",
        lazy="selectin",
    )
