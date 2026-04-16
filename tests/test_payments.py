from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.enums import OrderStatus, PaymentStatus, UserRole
from app.models.order import Order
from app.models.payment import Payment
from app.models.product_item import ProductItem
from app.models.stock_movement import StockMovement
from app.services.payment_service import MercadoPagoGateway
from tests.conftest import AuthContext


async def create_category(client: AsyncClient, *, name: str = "Carregadores") -> dict:
    response = await client.post(
        "/api/v1/admin/categories",
        json={"name": name, "description": "Categoria base"},
    )
    assert response.status_code == 201
    return response.json()["data"]


async def create_product(
    client: AsyncClient,
    *,
    category_id: str,
    name_base: str = "Carregadores Motorola",
    brand: str = "Motorola",
) -> dict:
    response = await client.post(
        "/api/v1/admin/products",
        json={
            "category_id": category_id,
            "name_base": name_base,
            "brand": brand,
            "description": "Linha de carregadores turbo",
            "image_url": "https://example.com/produto.png",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


async def create_product_item(
    client: AsyncClient,
    *,
    product_id: str,
    internal_code: str,
    sku: str,
    price: str,
    stock_current: int,
    stock_minimum: int = 2,
) -> dict:
    response = await client.post(
        "/api/v1/admin/product-items",
        json={
            "product_id": product_id,
            "internal_code": internal_code,
            "sku": sku,
            "name": f"Item {internal_code}",
            "connector_type": "Tipo C",
            "power": "45W",
            "voltage": "220V",
            "short_description": f"descricao {internal_code}",
            "price": price,
            "stock_current": stock_current,
            "stock_minimum": stock_minimum,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


async def create_catalog_item_for_payment(
    client: AsyncClient,
    auth_context: AuthContext,
    *,
    internal_code: str = "CA700",
    sku: str = "WM-CA700",
    price: str = "79.90",
    stock_current: int = 10,
) -> dict:
    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    category = await create_category(client)
    product = await create_product(client, category_id=category["id"])
    return await create_product_item(
        client,
        product_id=product["id"],
        internal_code=internal_code,
        sku=sku,
        price=price,
        stock_current=stock_current,
    )


async def create_order_ready_for_payment(
    client: AsyncClient,
    auth_context: AuthContext,
    *,
    customer_email: str = "customer1@example.com",
    customer_id: uuid.UUID | None = None,
    quantity: int = 2,
    stock_current: int = 10,
) -> tuple[dict, dict, uuid.UUID]:
    item = await create_catalog_item_for_payment(
        client,
        auth_context=auth_context,
        stock_current=stock_current,
    )
    resolved_customer_id = customer_id or uuid.uuid4()
    auth_context.set_user(
        role=UserRole.CUSTOMER,
        email=customer_email,
        user_id=resolved_customer_id,
    )
    add_response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": quantity},
    )
    assert add_response.status_code == 200

    order_response = await client.post(
        "/api/v1/orders",
        json={"fulfillment_type": "pickup"},
    )
    assert order_response.status_code == 201
    return order_response.json()["data"], item, resolved_customer_id


@pytest.mark.asyncio
async def test_create_pix_payment(
    client: AsyncClient,
    auth_context: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, _, _ = await create_order_ready_for_payment(client, auth_context)

    async def fake_create_pix_payment(self, *, order, idempotency_key):  # type: ignore[no-untyped-def]
        return {
            "id": "mp-pix-001",
            "status": "pending",
            "transaction_amount": "159.80",
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code_base64": "base64-qr",
                    "qr_code": "pix-copia-cola",
                }
            },
        }

    monkeypatch.setattr(MercadoPagoGateway, "create_pix_payment", fake_create_pix_payment)

    response = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": order["id"]},
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["external_id"] == "mp-pix-001"
    assert payload["status"] == "pending"
    assert payload["qr_code"] == "base64-qr"
    assert payload["copy_paste_code"] == "pix-copia-cola"
    assert Decimal(payload["amount"]) == Decimal("159.80")


@pytest.mark.asyncio
async def test_webhook_approved_updates_order(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, item, _ = await create_order_ready_for_payment(client, auth_context)

    async def fake_create_pix_payment(self, *, order, idempotency_key):  # type: ignore[no-untyped-def]
        return {
            "id": "mp-pix-approve-001",
            "status": "pending",
            "transaction_amount": "159.80",
            "point_of_interaction": {"transaction_data": {"qr_code_base64": "qr", "qr_code": "copy"}},
        }

    async def fake_get_payment(self, external_id):  # type: ignore[no-untyped-def]
        assert external_id == "mp-pix-approve-001"
        return {
            "id": external_id,
            "status": "approved",
            "transaction_amount": "159.80",
        }

    monkeypatch.setattr(MercadoPagoGateway, "create_pix_payment", fake_create_pix_payment)
    monkeypatch.setattr(MercadoPagoGateway, "get_payment", fake_get_payment)

    create_payment = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": order["id"]},
    )
    assert create_payment.status_code == 201

    webhook_response = await client.post(
        "/api/v1/payments/mercadopago/webhook",
        json={"id": "evt-001", "type": "payment", "data": {"id": "mp-pix-approve-001"}},
    )
    assert webhook_response.status_code == 200
    assert webhook_response.json()["data"]["processed"] is True

    async with db_session_factory() as session:
        saved_order = await session.scalar(select(Order).where(Order.id == uuid.UUID(order["id"])))
        saved_payment = await session.scalar(
            select(Payment).where(Payment.external_id == "mp-pix-approve-001")
        )
        saved_item = await session.scalar(
            select(ProductItem).where(ProductItem.id == uuid.UUID(item["id"]))
        )
        movement_count = await session.scalar(select(func.count(StockMovement.id)))

        assert saved_order is not None
        assert saved_payment is not None
        assert saved_item is not None
        assert saved_order.payment_status == PaymentStatus.APPROVED
        assert saved_order.order_status == OrderStatus.PAID
        assert saved_payment.status == PaymentStatus.APPROVED
        assert saved_item.stock_current == 8
        assert int(movement_count or 0) == 1


@pytest.mark.asyncio
async def test_webhook_duplicate_is_ignored(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, item, _ = await create_order_ready_for_payment(client, auth_context)

    async def fake_create_pix_payment(self, *, order, idempotency_key):  # type: ignore[no-untyped-def]
        return {
            "id": "mp-pix-dup-001",
            "status": "pending",
            "transaction_amount": "159.80",
            "point_of_interaction": {"transaction_data": {"qr_code_base64": "qr", "qr_code": "copy"}},
        }

    async def fake_get_payment(self, external_id):  # type: ignore[no-untyped-def]
        return {
            "id": external_id,
            "status": "approved",
            "transaction_amount": "159.80",
        }

    monkeypatch.setattr(MercadoPagoGateway, "create_pix_payment", fake_create_pix_payment)
    monkeypatch.setattr(MercadoPagoGateway, "get_payment", fake_get_payment)

    create_payment = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": order["id"]},
    )
    assert create_payment.status_code == 201

    first_webhook = await client.post(
        "/api/v1/payments/mercadopago/webhook",
        json={"id": "evt-dup-001", "type": "payment", "data": {"id": "mp-pix-dup-001"}},
    )
    second_webhook = await client.post(
        "/api/v1/payments/mercadopago/webhook",
        json={"id": "evt-dup-001", "type": "payment", "data": {"id": "mp-pix-dup-001"}},
    )

    assert first_webhook.status_code == 200
    assert second_webhook.status_code == 200
    assert second_webhook.json()["data"]["ignored"] is True

    async with db_session_factory() as session:
        saved_item = await session.scalar(
            select(ProductItem).where(ProductItem.id == uuid.UUID(item["id"]))
        )
        movement_count = await session.scalar(select(func.count(StockMovement.id)))

        assert saved_item is not None
        assert saved_item.stock_current == 8
        assert int(movement_count or 0) == 1


@pytest.mark.asyncio
async def test_payment_rejected_updates_status(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, _, _ = await create_order_ready_for_payment(client, auth_context)

    async def fake_create_pix_payment(self, *, order, idempotency_key):  # type: ignore[no-untyped-def]
        return {
            "id": "mp-pix-rejected-001",
            "status": "pending",
            "transaction_amount": "159.80",
            "point_of_interaction": {"transaction_data": {"qr_code_base64": "qr", "qr_code": "copy"}},
        }

    async def fake_get_payment(self, external_id):  # type: ignore[no-untyped-def]
        return {
            "id": external_id,
            "status": "rejected",
            "transaction_amount": "159.80",
        }

    monkeypatch.setattr(MercadoPagoGateway, "create_pix_payment", fake_create_pix_payment)
    monkeypatch.setattr(MercadoPagoGateway, "get_payment", fake_get_payment)

    create_payment = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": order["id"]},
    )
    assert create_payment.status_code == 201

    webhook_response = await client.post(
        "/api/v1/payments/mercadopago/webhook",
        json={"id": "evt-rej-001", "type": "payment", "data": {"id": "mp-pix-rejected-001"}},
    )
    assert webhook_response.status_code == 200

    async with db_session_factory() as session:
        saved_order = await session.scalar(select(Order).where(Order.id == uuid.UUID(order["id"])))
        saved_payment = await session.scalar(
            select(Payment).where(Payment.external_id == "mp-pix-rejected-001")
        )

        assert saved_order is not None
        assert saved_payment is not None
        assert saved_order.payment_status == PaymentStatus.REJECTED
        assert saved_order.order_status == OrderStatus.WAITING_PAYMENT
        assert saved_payment.status == PaymentStatus.REJECTED


@pytest.mark.asyncio
async def test_prevent_paying_order_already_paid(
    client: AsyncClient,
    auth_context: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, _, _ = await create_order_ready_for_payment(client, auth_context)

    async def fake_create_pix_payment(self, *, order, idempotency_key):  # type: ignore[no-untyped-def]
        return {
            "id": "mp-pix-paid-001",
            "status": "pending",
            "transaction_amount": "159.80",
            "point_of_interaction": {"transaction_data": {"qr_code_base64": "qr", "qr_code": "copy"}},
        }

    async def fake_get_payment(self, external_id):  # type: ignore[no-untyped-def]
        return {
            "id": external_id,
            "status": "approved",
            "transaction_amount": "159.80",
        }

    monkeypatch.setattr(MercadoPagoGateway, "create_pix_payment", fake_create_pix_payment)
    monkeypatch.setattr(MercadoPagoGateway, "get_payment", fake_get_payment)

    first_payment = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": order["id"]},
    )
    assert first_payment.status_code == 201

    webhook_response = await client.post(
        "/api/v1/payments/mercadopago/webhook",
        json={"id": "evt-paid-001", "type": "payment", "data": {"id": "mp-pix-paid-001"}},
    )
    assert webhook_response.status_code == 200

    second_payment = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": order["id"]},
    )

    assert second_payment.status_code == 400
    assert second_payment.json()["code"] == "business_rule_error"


@pytest.mark.asyncio
async def test_prevent_paying_invalid_order(
    client: AsyncClient,
    auth_context: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")

    async def fake_create_pix_payment(self, *, order, idempotency_key):  # type: ignore[no-untyped-def]
        return {
            "id": "unused",
            "status": "pending",
            "transaction_amount": "1.00",
            "point_of_interaction": {"transaction_data": {"qr_code_base64": "qr", "qr_code": "copy"}},
        }

    monkeypatch.setattr(MercadoPagoGateway, "create_pix_payment", fake_create_pix_payment)

    response = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": str(uuid.uuid4())},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "not_found_error"
