from __future__ import annotations

import hashlib
import hmac
import json
from copy import deepcopy
from decimal import Decimal
from logging import getLogger
from typing import Any
from uuid import UUID, uuid4

import httpx
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, ExternalServiceError, NotFoundError
from app.models.enums import (
    OrderStatus,
    PaymentMethod,
    PaymentProvider,
    PaymentStatus,
    StockMovementSource,
    StockMovementType,
    UserRole,
)
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.repositories.order_status_history_repository import OrderStatusHistoryRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.product_item_repository import ProductItemRepository
from app.repositories.stock_movement_repository import StockMovementRepository
from app.schemas.payment import (
    MercadoPagoCardPaymentCreate,
    MercadoPagoPixPaymentCreate,
    PaymentWebhookProcessResponse,
)
from app.utils.audit import AuditAction, register_audit_event

logger = getLogger(__name__)


class MercadoPagoGateway:
    def __init__(self) -> None:
        self.base_url = settings.mercadopago_base_url.rstrip("/")
        self.access_token = settings.mercadopago_access_token
        self.timeout_seconds = settings.mercadopago_timeout_seconds

    async def create_pix_payment(
        self,
        *,
        order: Order,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "transaction_amount": float(order.total),
            "payment_method_id": PaymentMethod.PIX.value,
            "description": f"Pedido WM Distribuidora {order.id}",
            "external_reference": str(order.id),
            "payer": {"email": order.user.email},
        }
        if settings.mercadopago_notification_url:
            payload["notification_url"] = settings.mercadopago_notification_url

        return await self._post_payment(payload=payload, idempotency_key=idempotency_key)

    async def create_card_payment(
        self,
        *,
        order: Order,
        payload: MercadoPagoCardPaymentCreate,
        idempotency_key: str,
    ) -> dict[str, Any]:
        request_payload: dict[str, Any] = {
            "transaction_amount": float(order.total),
            "token": payload.card_token,
            "installments": payload.installments,
            "payment_method_id": payload.payment_method_id,
            "description": f"Pedido WM Distribuidora {order.id}",
            "external_reference": str(order.id),
            "payer": {"email": order.user.email},
        }
        if settings.mercadopago_notification_url:
            request_payload["notification_url"] = settings.mercadopago_notification_url

        return await self._post_payment(payload=request_payload, idempotency_key=idempotency_key)

    async def get_payment(self, external_id: str) -> dict[str, Any]:
        response = await self._request("GET", f"/v1/payments/{external_id}")
        return response.json()

    async def _post_payment(
        self,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/v1/payments",
            json=payload,
            headers={"X-Idempotency-Key": idempotency_key},
        )
        return response.json()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        if not self.access_token:
            raise ExternalServiceError("Mercado Pago access token is not configured")

        merged_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if headers is not None:
            merged_headers.update(headers)

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=merged_headers,
                    json=json,
                )
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                detail = self._extract_provider_error(exc.response)
                raise ExternalServiceError(detail) from exc
            except httpx.HTTPError as exc:
                raise ExternalServiceError("Mercado Pago request failed") from exc

    def _extract_provider_error(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return f"Mercado Pago request failed with status {response.status_code}"

        message = payload.get("message") or payload.get("error") or payload.get("cause")
        if isinstance(message, list) and message:
            return str(message[0])
        if message:
            return f"Mercado Pago request failed: {message}"
        return f"Mercado Pago request failed with status {response.status_code}"


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.gateway = MercadoPagoGateway()
        self.order_repository = OrderRepository(session)
        self.order_status_history_repository = OrderStatusHistoryRepository(session)
        self.payment_repository = PaymentRepository(session)
        self.product_item_repository = ProductItemRepository(session)
        self.stock_movement_repository = StockMovementRepository(session)

    async def create_pix_payment(self, user: User, payload: MercadoPagoPixPaymentCreate) -> Payment:
        order = await self._get_customer_order_for_payment(user, payload.order_id)
        self._ensure_order_can_be_paid(order)
        await self._ensure_no_open_payment(order.id)

        idempotency_key = str(uuid4())
        provider_response = await self.gateway.create_pix_payment(
            order=order,
            idempotency_key=idempotency_key,
        )
        payment = await self._create_local_payment(
            order=order,
            method=PaymentMethod.PIX,
            provider_response=provider_response,
            idempotency_key=idempotency_key,
        )
        await self._synchronize_provider_state(payment, provider_response)
        await register_audit_event(
            self.session,
            action=AuditAction.PAYMENT_CREATED,
            actor=user,
            entity="payment",
            entity_id=payment.id,
            metadata={
                "provider": payment.provider.value,
                "method": payment.method.value,
                "order_id": str(payment.order_id),
                "external_id": payment.external_id,
            },
        )
        await self.session.commit()
        payment = await self._get_payment(payment.id)
        return payment

    async def create_card_payment(self, user: User, payload: MercadoPagoCardPaymentCreate) -> Payment:
        order = await self._get_customer_order_for_payment(user, payload.order_id)
        self._ensure_order_can_be_paid(order)
        await self._ensure_no_open_payment(order.id)

        idempotency_key = str(uuid4())
        provider_response = await self.gateway.create_card_payment(
            order=order,
            payload=payload,
            idempotency_key=idempotency_key,
        )
        payment = await self._create_local_payment(
            order=order,
            method=PaymentMethod.CARD,
            provider_response=provider_response,
            idempotency_key=idempotency_key,
        )
        await self._synchronize_provider_state(payment, provider_response)
        await register_audit_event(
            self.session,
            action=AuditAction.PAYMENT_CREATED,
            actor=user,
            entity="payment",
            entity_id=payment.id,
            metadata={
                "provider": payment.provider.value,
                "method": payment.method.value,
                "order_id": str(payment.order_id),
                "external_id": payment.external_id,
            },
        )
        await self.session.commit()
        payment = await self._get_payment(payment.id)
        return payment

    async def handle_mercadopago_webhook(self, request: Request) -> PaymentWebhookProcessResponse:
        payload = await self._load_webhook_payload(request)
        external_id = self._extract_external_payment_id(payload, request)
        notification_id = self._extract_notification_id(payload)

        await self._validate_webhook_signature(request, external_id)

        payment = await self.payment_repository.get_by_external_id(external_id)
        if payment is None:
            logger.warning("Mercado Pago webhook ignored: local payment not found for %s", external_id)
            return PaymentWebhookProcessResponse(
                processed=False,
                ignored=True,
                message="Payment not found locally",
            )

        if notification_id is not None and self._notification_already_processed(payment, notification_id):
            logger.info("Mercado Pago webhook duplicate ignored for payment %s", payment.id)
            self._append_processed_notification(payment, notification_id)
            await self.session.commit()
            return PaymentWebhookProcessResponse(
                processed=False,
                ignored=True,
                payment_id=payment.id,
                order_id=payment.order_id,
                message="Duplicate webhook ignored",
            )

        provider_response = await self.gateway.get_payment(external_id)
        await self._synchronize_provider_state(
            payment,
            provider_response,
            notification_id=notification_id,
        )
        await self.session.commit()

        return PaymentWebhookProcessResponse(
            processed=True,
            ignored=False,
            payment_id=payment.id,
            order_id=payment.order_id,
            message="Webhook processed successfully",
        )

    async def _create_local_payment(
        self,
        *,
        order: Order,
        method: PaymentMethod,
        provider_response: dict[str, Any],
        idempotency_key: str,
    ) -> Payment:
        transaction_data = (
            provider_response.get("point_of_interaction", {})
            .get("transaction_data", {})
        )
        self._validate_provider_amount(order.total, provider_response)
        payment = await self.payment_repository.create(
            order_id=order.id,
            provider=PaymentProvider.MERCADOPAGO,
            method=method,
            status=self._map_provider_status(provider_response.get("status")),
            amount=order.total,
            external_id=self._extract_provider_external_id(provider_response),
            qr_code=transaction_data.get("qr_code_base64"),
            copy_paste_code=transaction_data.get("qr_code"),
            provider_payload={
                "idempotency_key": idempotency_key,
                "provider_response": provider_response,
                "processed_notification_ids": [],
                "stock_applied": False,
            },
        )
        return payment

    async def _synchronize_provider_state(
        self,
        payment: Payment,
        provider_response: dict[str, Any],
        *,
        notification_id: str | None = None,
    ) -> None:
        order = await self._get_order(payment.order_id)
        normalized_status = self._map_provider_status(provider_response.get("status"))
        self._validate_provider_amount(order.total, provider_response)

        payment.external_id = self._extract_provider_external_id(provider_response)
        payment.status = normalized_status
        payment.amount = order.total
        self._merge_provider_payload(payment, provider_response, notification_id)

        if normalized_status == PaymentStatus.APPROVED:
            if self._stock_already_applied(payment) and order.order_status == OrderStatus.PAID:
                return
            stock_applied = await self._apply_stock_deduction(payment)
            order.payment_status = PaymentStatus.APPROVED
            if stock_applied:
                previous_status = order.order_status
                order.order_status = OrderStatus.PAID
                await self._register_order_status_change(
                    order=order,
                    previous_status=previous_status,
                    new_status=OrderStatus.PAID,
                    actor=None,
                )
                await register_audit_event(
                    self.session,
                    action=AuditAction.PAYMENT_APPROVED,
                    actor=order.user,
                    entity="payment",
                    entity_id=payment.id,
                    metadata={"order_id": str(order.id), "external_id": payment.external_id},
                )
            else:
                await register_audit_event(
                    self.session,
                    action=AuditAction.PAYMENT_STOCK_CONFIRMATION_ERROR,
                    actor=order.user,
                    entity="payment",
                    entity_id=payment.id,
                    metadata={"order_id": str(order.id), "external_id": payment.external_id},
                )
        elif normalized_status == PaymentStatus.REJECTED:
            order.payment_status = PaymentStatus.REJECTED
            await register_audit_event(
                self.session,
                action=AuditAction.PAYMENT_REJECTED,
                actor=order.user,
                entity="payment",
                entity_id=payment.id,
                metadata={"order_id": str(order.id), "external_id": payment.external_id},
            )
        elif normalized_status == PaymentStatus.CANCELLED:
            order.payment_status = PaymentStatus.CANCELLED
            await register_audit_event(
                self.session,
                action=AuditAction.PAYMENT_CANCELLED,
                actor=order.user,
                entity="payment",
                entity_id=payment.id,
                metadata={"order_id": str(order.id), "external_id": payment.external_id},
            )
        else:
            order.payment_status = normalized_status

    async def _apply_stock_deduction(self, payment: Payment) -> bool:
        provider_payload = deepcopy(payment.provider_payload or {})
        if provider_payload.get("stock_applied") is True:
            return True

        order = await self._get_order(payment.order_id)
        for order_item in order.items:
            product_item = await self.product_item_repository.get_by_id(order_item.product_item_id)
            if product_item is None:
                logger.critical("Payment %s approval failed: product item missing", payment.id)
                provider_payload["stock_error"] = "Product item missing during payment confirmation"
                payment.provider_payload = provider_payload
                return False
            if product_item.stock_current < order_item.quantity:
                logger.critical(
                    "Payment %s approval failed: insufficient stock for product item %s",
                    payment.id,
                    product_item.id,
                )
                provider_payload["stock_error"] = (
                    f"Insufficient stock for product item {product_item.id} during payment confirmation"
                )
                payment.provider_payload = provider_payload
                return False

        for order_item in order.items:
            product_item = await self.product_item_repository.get_by_id(order_item.product_item_id)
            if product_item is None:
                raise NotFoundError("Product item not found")

            previous_stock = product_item.stock_current
            product_item.stock_current = previous_stock - order_item.quantity
            await self.stock_movement_repository.create(
                product_item_id=product_item.id,
                order_id=order.id,
                payment_id=payment.id,
                movement_type=StockMovementType.SALE,
                quantity=order_item.quantity,
                source=StockMovementSource.ORDER,
                reference_id=order.id,
                performed_by_user_id=order.assigned_employee_id,
                previous_stock=previous_stock,
                new_stock=product_item.stock_current,
                reason=f"Payment approved for order {order.id}",
            )

        provider_payload["stock_applied"] = True
        provider_payload.pop("stock_error", None)
        payment.provider_payload = provider_payload
        return True

    async def _ensure_no_open_payment(self, order_id: UUID) -> None:
        existing_payment = await self.payment_repository.get_latest_open_by_order_id(order_id)
        if existing_payment is not None:
            raise BusinessRuleError("This order already has an active payment attempt")

    async def _get_customer_order_for_payment(self, user: User, order_id: UUID) -> Order:
        if user.role != UserRole.CUSTOMER:
            raise BusinessRuleError("Only customers can create payments")

        order = await self.order_repository.get_by_user_and_id(user.id, order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    async def _get_order(self, order_id: UUID) -> Order:
        order = await self.order_repository.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    async def _get_payment(self, payment_id: UUID) -> Payment:
        payment = await self.payment_repository.get_by_id(payment_id)
        if payment is None:
            raise NotFoundError("Payment not found")
        return payment

    async def _register_order_status_change(
        self,
        *,
        order: Order,
        previous_status: OrderStatus | None,
        new_status: OrderStatus,
        actor: User | None,
    ) -> None:
        if previous_status == new_status:
            return
        await self.order_status_history_repository.create(
            order_id=order.id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by_user_id=actor.id if actor is not None else None,
        )
        await register_audit_event(
            self.session,
            action=AuditAction.ORDER_STATUS_CHANGED,
            actor=actor,
            entity="order",
            entity_id=order.id,
            metadata={
                "previous_status": previous_status.value if previous_status is not None else None,
                "new_status": new_status.value,
            },
        )

    def _ensure_order_can_be_paid(self, order: Order) -> None:
        if order.order_status != OrderStatus.WAITING_PAYMENT:
            raise BusinessRuleError("This order cannot receive a new payment")
        if order.payment_status == PaymentStatus.APPROVED:
            raise BusinessRuleError("This order is already paid")

    def _map_provider_status(self, provider_status: str | None) -> PaymentStatus:
        if provider_status == "approved":
            return PaymentStatus.APPROVED
        if provider_status == "rejected":
            return PaymentStatus.REJECTED
        if provider_status in {"cancelled", "canceled"}:
            return PaymentStatus.CANCELLED
        if provider_status == "authorized":
            return PaymentStatus.AUTHORIZED
        if provider_status == "refunded":
            return PaymentStatus.REFUNDED
        if provider_status == "paid":
            return PaymentStatus.PAID
        if provider_status == "failed":
            return PaymentStatus.FAILED
        return PaymentStatus.PENDING

    def _extract_provider_external_id(self, provider_response: dict[str, Any]) -> str:
        raw_id = provider_response.get("id")
        if raw_id is None:
            raise ExternalServiceError("Mercado Pago did not return a payment identifier")
        return str(raw_id)

    def _validate_provider_amount(
        self,
        expected_amount: Decimal,
        provider_response: dict[str, Any],
    ) -> None:
        transaction_amount = provider_response.get("transaction_amount")
        if transaction_amount is None:
            return

        normalized_amount = Decimal(str(transaction_amount))
        if normalized_amount != expected_amount:
            raise ExternalServiceError("Mercado Pago returned a payment amount different from the order total")

    def _merge_provider_payload(
        self,
        payment: Payment,
        provider_response: dict[str, Any],
        notification_id: str | None,
    ) -> None:
        payload = deepcopy(payment.provider_payload or {})
        payload["provider_response"] = provider_response
        payload["provider_status"] = provider_response.get("status")
        payload.setdefault("processed_notification_ids", [])
        payload.setdefault("stock_applied", False)
        if notification_id is not None and notification_id not in payload["processed_notification_ids"]:
            payload["processed_notification_ids"].append(notification_id)
        payment.provider_payload = payload

    def _notification_already_processed(self, payment: Payment, notification_id: str) -> bool:
        payload = payment.provider_payload or {}
        processed_ids = payload.get("processed_notification_ids", [])
        return notification_id in processed_ids

    def _append_processed_notification(self, payment: Payment, notification_id: str) -> None:
        payload = deepcopy(payment.provider_payload or {})
        processed_ids = payload.setdefault("processed_notification_ids", [])
        if notification_id not in processed_ids:
            processed_ids.append(notification_id)
        payment.provider_payload = payload

    def _stock_already_applied(self, payment: Payment) -> bool:
        payload = payment.provider_payload or {}
        return payload.get("stock_applied") is True

    async def _load_webhook_payload(self, request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
        except json.JSONDecodeError as exc:
            raise BusinessRuleError("Invalid webhook payload") from exc

        if not isinstance(payload, dict):
            raise BusinessRuleError("Invalid webhook payload")
        return payload

    def _extract_external_payment_id(self, payload: dict[str, Any], request: Request) -> str:
        external_id = (
            request.query_params.get("data.id")
            or request.query_params.get("id")
            or payload.get("data", {}).get("id")
        )
        if external_id is None:
            raise BusinessRuleError("Webhook payload does not contain a payment identifier")
        return str(external_id)

    def _extract_notification_id(self, payload: dict[str, Any]) -> str | None:
        notification_id = payload.get("id")
        return str(notification_id) if notification_id is not None else None

    async def _validate_webhook_signature(self, request: Request, external_id: str) -> None:
        secret = settings.mercadopago_webhook_secret
        signature_header = request.headers.get("x-signature")
        request_id = request.headers.get("x-request-id")

        if not secret:
            logger.warning("Mercado Pago webhook secret not configured; signature validation skipped")
            return

        if not signature_header or not request_id:
            raise BusinessRuleError("Missing Mercado Pago webhook signature headers")

        parts = dict(
            part.split("=", maxsplit=1)
            for part in signature_header.split(",")
            if "=" in part
        )
        ts = parts.get("ts")
        received_hash = parts.get("v1")
        if not ts or not received_hash:
            raise BusinessRuleError("Invalid Mercado Pago webhook signature")

        manifest = f"id:{external_id};request-id:{request_id};ts:{ts};"
        expected_hash = hmac.new(
            secret.encode("utf-8"),
            msg=manifest.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_hash, received_hash):
            raise BusinessRuleError("Invalid Mercado Pago webhook signature")
