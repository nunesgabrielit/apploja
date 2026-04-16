from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from app.models.enums import PaymentMethod, PaymentProvider, PaymentStatus

CardTokenStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]
PaymentMethodIdStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
]


class MercadoPagoPixPaymentCreate(BaseModel):
    order_id: UUID


class MercadoPagoCardPaymentCreate(BaseModel):
    order_id: UUID
    card_token: CardTokenStr
    installments: int = Field(ge=1, le=24)
    payment_method_id: PaymentMethodIdStr


class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    provider: PaymentProvider
    method: PaymentMethod
    external_id: str | None
    status: PaymentStatus
    amount: Decimal
    qr_code: str | None
    copy_paste_code: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, payment: object) -> "PaymentResponse":
        return cls(
            id=payment.id,
            order_id=payment.order_id,
            provider=payment.provider,
            method=payment.method,
            external_id=payment.external_id,
            status=payment.status,
            amount=payment.amount,
            qr_code=payment.qr_code,
            copy_paste_code=payment.copy_paste_code,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )


class PaymentWebhookProcessResponse(BaseModel):
    processed: bool
    ignored: bool
    payment_id: UUID | None = None
    order_id: UUID | None = None
    message: str
