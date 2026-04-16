from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import CartStatus

if TYPE_CHECKING:
    from app.models.cart_item import CartItem
    from app.models.user import User


class Cart(TimestampMixin, Base):
    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[CartStatus] = mapped_column(
        Enum(
            CartStatus,
            name="cart_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=CartStatus.ACTIVE,
    )

    user: Mapped[User] = relationship(
        back_populates="carts",
        lazy="selectin",
    )
    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CartItem.created_at.asc()",
    )
