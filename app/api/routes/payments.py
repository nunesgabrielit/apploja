from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.core.dependencies import CurrentCustomerDep, DBSession
from app.schemas.common import ApiResponse
from app.schemas.payment import (
    MercadoPagoCardPaymentCreate,
    MercadoPagoPixPaymentCreate,
    PaymentResponse,
    PaymentWebhookProcessResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/mercadopago/pix",
    response_model=ApiResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_mercadopago_pix_payment(
    payload: MercadoPagoPixPaymentCreate,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[PaymentResponse]:
    payment = await PaymentService(session).create_pix_payment(current_user, payload)
    return ApiResponse[PaymentResponse](
        message="PIX payment created successfully",
        data=PaymentResponse.from_model(payment),
    )


@router.post(
    "/mercadopago/card",
    response_model=ApiResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_mercadopago_card_payment(
    payload: MercadoPagoCardPaymentCreate,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[PaymentResponse]:
    payment = await PaymentService(session).create_card_payment(current_user, payload)
    return ApiResponse[PaymentResponse](
        message="Card payment created successfully",
        data=PaymentResponse.from_model(payment),
    )


@router.post("/mercadopago/webhook", response_model=ApiResponse[PaymentWebhookProcessResponse])
async def mercadopago_webhook(
    request: Request,
    session: DBSession,
) -> ApiResponse[PaymentWebhookProcessResponse]:
    result = await PaymentService(session).handle_mercadopago_webhook(request)
    return ApiResponse[PaymentWebhookProcessResponse](
        message="Webhook received successfully",
        data=result,
    )
