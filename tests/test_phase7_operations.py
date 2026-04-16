from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit_log import AuditLog
from app.models.enums import OrderStatus, PaymentStatus, StockMovementType, UserRole
from app.models.order import Order
from app.models.order_status_history import OrderStatusHistory
from app.models.product_item import ProductItem
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.services.payment_service import MercadoPagoGateway
from tests.conftest import AuthContext
from tests.test_orders import (
    add_item_to_customer_cart,
    create_catalog_item_for_order,
    create_category,
    create_product,
    create_product_item,
)


async def create_order_for_phase7(
    client: AsyncClient,
    auth_context: AuthContext,
    *,
    customer_email: str,
    customer_id: uuid.UUID | None = None,
    quantity: int = 2,
    stock_current: int = 20,
) -> tuple[dict, dict]:
    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    category = await create_category(client, name=f"Categoria-{uuid.uuid4()}")
    product = await create_product(
        client,
        category_id=category["id"],
        name_base=f"Produto-{uuid.uuid4()}",
        brand="Marca Fase7",
    )
    item = await create_product_item(
        client,
        product_id=product["id"],
        internal_code=f"CA-{str(uuid.uuid4())[:8]}",
        sku=f"SKU-{str(uuid.uuid4())[:8]}",
        price="79.90",
        stock_current=stock_current,
    )
    await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email=customer_email,
        customer_id=customer_id,
        product_item_id=item["id"],
        quantity=quantity,
    )
    create_response = await client.post("/api/v1/orders", json={"fulfillment_type": "pickup"})
    assert create_response.status_code == 201
    return create_response.json()["data"], item


@pytest.mark.asyncio
async def test_order_status_history_endpoint_registers_payment_and_cancellation(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, _ = await create_order_for_phase7(
        client,
        auth_context,
        customer_email="history.customer@example.com",
    )

    async def fake_create_pix_payment(self, *, order, idempotency_key):  # type: ignore[no-untyped-def]
        return {
            "id": "mp-phase7-history-001",
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

    pay_response = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": order["id"]},
    )
    assert pay_response.status_code == 201

    webhook_response = await client.post(
        "/api/v1/payments/mercadopago/webhook",
        json={"id": "evt-phase7-history-001", "type": "payment", "data": {"id": "mp-phase7-history-001"}},
    )
    assert webhook_response.status_code == 200

    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    cancel_response = await client.post(f"/api/v1/admin/orders/{order['id']}/cancel")
    assert cancel_response.status_code == 200

    history_response = await client.get(f"/api/v1/admin/orders/{order['id']}/history")
    assert history_response.status_code == 200
    history_items = history_response.json()["data"]
    assert len(history_items) == 2
    assert history_items[0]["previous_status"] == "waiting_payment"
    assert history_items[0]["new_status"] == "paid"
    assert history_items[1]["previous_status"] == "paid"
    assert history_items[1]["new_status"] == "cancelled"

    async with db_session_factory() as session:
        count = await session.scalar(
            select(OrderStatusHistory).where(OrderStatusHistory.order_id == uuid.UUID(order["id"]))
        )
        assert count is not None


@pytest.mark.asyncio
async def test_manual_stock_adjustment_creates_movement_and_audit(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    item = await create_catalog_item_for_order(
        client,
        auth_context=auth_context,
        internal_code="CA-PHASE7-MANUAL",
        sku="WM-PHASE7-MANUAL",
        stock_current=12,
    )

    update_response = await client.patch(
        f"/api/v1/admin/product-items/{item['id']}/stock",
        json={"quantity": 4, "operation": "decrement", "reason": "contagem manual"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["stock_current"] == 8

    async with db_session_factory() as session:
        movements = (
            await session.execute(
                select(StockMovement).where(StockMovement.product_item_id == uuid.UUID(item["id"]))
            )
        ).scalars().all()
        stock_audits = (
            await session.execute(
                select(AuditLog).where(AuditLog.action == "product_item_stock_updated")
            )
        ).scalars().all()

        assert len(movements) == 1
        assert movements[0].movement_type.value == "manual_adjustment"
        assert movements[0].source.value == "admin"
        assert movements[0].performed_by_user_id is not None
        assert len(stock_audits) >= 1


@pytest.mark.asyncio
async def test_product_create_and_edit_are_persisted_in_audit_log(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    category = await create_category(client, name="Fase7 Auditoria Produtos")
    product = await create_product(
        client,
        category_id=category["id"],
        name_base="Produto Auditoria",
        brand="Marca Auditoria",
    )

    update_response = await client.put(
        f"/api/v1/admin/products/{product['id']}",
        json={
            "name_base": "Produto Auditoria Atualizado",
            "brand": "Marca Auditoria",
            "description": "Produto atualizado",
            "image_url": "https://example.com/produto-auditado.png",
        },
    )
    assert update_response.status_code == 200

    async with db_session_factory() as session:
        create_audit = await session.scalar(
            select(AuditLog).where(
                AuditLog.action == "product_created",
                AuditLog.entity_id == uuid.UUID(product["id"]),
            )
        )
        update_audit = await session.scalar(
            select(AuditLog).where(
                AuditLog.action == "product_updated",
                AuditLog.entity_id == uuid.UUID(product["id"]),
            )
        )
        assert create_audit is not None
        assert update_audit is not None


@pytest.mark.asyncio
async def test_cancel_paid_order_returns_stock_and_creates_return_movement(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order, item = await create_order_for_phase7(
        client,
        auth_context,
        customer_email="cancel.customer@example.com",
    )

    async def fake_create_pix_payment(self, *, order, idempotency_key):  # type: ignore[no-untyped-def]
        return {
            "id": "mp-phase7-cancel-001",
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

    pay_response = await client.post(
        "/api/v1/payments/mercadopago/pix",
        json={"order_id": order["id"]},
    )
    assert pay_response.status_code == 201

    webhook_response = await client.post(
        "/api/v1/payments/mercadopago/webhook",
        json={"id": "evt-phase7-cancel-001", "type": "payment", "data": {"id": "mp-phase7-cancel-001"}},
    )
    assert webhook_response.status_code == 200

    auth_context.set_user(role=UserRole.EMPLOYEE, email="employee@example.com")
    forbidden_cancel = await client.post(f"/api/v1/admin/orders/{order['id']}/cancel")
    assert forbidden_cancel.status_code == 403

    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    cancel_response = await client.post(f"/api/v1/admin/orders/{order['id']}/cancel?return_to_stock=true")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["data"]["order_status"] == "cancelled"

    async with db_session_factory() as session:
        saved_order = await session.scalar(select(Order).where(Order.id == uuid.UUID(order["id"])))
        saved_item = await session.scalar(
            select(ProductItem).where(ProductItem.id == uuid.UUID(item["id"]))
        )
        return_movements = (
            await session.execute(
                select(StockMovement).where(
                    StockMovement.order_id == uuid.UUID(order["id"]),
                    StockMovement.movement_type == StockMovementType.RETURN,
                )
            )
        ).scalars().all()
        cancel_audits = (
            await session.execute(select(AuditLog).where(AuditLog.action == "order_cancelled"))
        ).scalars().all()

        assert saved_order is not None
        assert saved_item is not None
        assert saved_order.order_status == OrderStatus.CANCELLED
        assert saved_order.payment_status == PaymentStatus.APPROVED
        assert saved_item.stock_current == 20
        assert len(return_movements) == 1
        assert len(cancel_audits) >= 1


@pytest.mark.asyncio
async def test_employee_performance_endpoint(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    employee_id = uuid.uuid4()
    order_one, _ = await create_order_for_phase7(
        client,
        auth_context,
        customer_email="perf1.customer@example.com",
        customer_id=uuid.uuid4(),
        quantity=1,
    )
    order_two, _ = await create_order_for_phase7(
        client,
        auth_context,
        customer_email="perf2.customer@example.com",
        customer_id=uuid.uuid4(),
        quantity=2,
    )

    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")

    async with db_session_factory() as session:
        session.add(
            User(
                id=employee_id,
                name="Funcionario Performance",
                email="employee.performance@example.com",
                phone="69999999999",
                password_hash="not-used",
                role=UserRole.EMPLOYEE,
                is_active=True,
            )
        )
        first = await session.scalar(select(Order).where(Order.id == uuid.UUID(order_one["id"])))
        second = await session.scalar(select(Order).where(Order.id == uuid.UUID(order_two["id"])))
        assert first is not None
        assert second is not None
        first.assigned_employee_id = employee_id
        second.assigned_employee_id = employee_id
        first.order_status = OrderStatus.PROCESSING
        first.payment_status = PaymentStatus.APPROVED
        second.order_status = OrderStatus.DELIVERED
        second.payment_status = PaymentStatus.APPROVED
        await session.commit()

    performance_response = await client.get("/api/v1/admin/employees/performance")
    assert performance_response.status_code == 200
    payload = performance_response.json()["data"]
    employee_metrics = next(item for item in payload if item["employee_id"] == str(employee_id))

    assert employee_metrics["assigned_orders"] == 2
    assert employee_metrics["processed_orders"] == 2
    assert employee_metrics["completed_orders"] == 1
    assert Decimal(employee_metrics["total_sold"]) > Decimal("0.00")
