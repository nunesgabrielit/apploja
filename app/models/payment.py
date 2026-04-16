from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, Enum, ForeignKey, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import PaymentMethod, PaymentProvider, PaymentStatus

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.stock_movement import StockMovement


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="payments_amount_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(
            PaymentProvider,
            name="payment_provider_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=PaymentProvider.MERCADOPAGO,
    )
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(
            PaymentMethod,
            name="payment_method_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True, index=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="payment_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    copy_paste_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    order: Mapped[Order] = relationship(
        back_populates="payments",
        lazy="selectin",
    )
    stock_movements: Mapped[list[StockMovement]] = relationship(
        back_populates="payment",
        lazy="selectin",
    )
