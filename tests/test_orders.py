from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.address import Address
from app.models.cart import Cart
from app.models.enums import CartStatus, UserRole
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
    stock_minimum: int = 5,
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


async def create_shipping_rule(client: AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/admin/shipping-rules",
        json={
            "zip_code_start": "69900000",
            "zip_code_end": "69900999",
            "rule_name": "Centro Rio Branco",
            "shipping_price": "19.90",
            "estimated_time_text": "2 dias uteis",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


async def create_address(
    db_session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    zip_code: str = "69900050",
) -> Address:
    async with db_session_factory() as session:
        address = Address(
            user_id=user_id,
            recipient_name="Cliente Teste",
            zip_code=zip_code,
            street="Rua A",
            number="123",
            district="Centro",
            city="Rio Branco",
            state="AC",
            complement=None,
            is_active=True,
        )
        session.add(address)
        await session.commit()
        await session.refresh(address)
        return address


async def create_catalog_item_for_order(
    client: AsyncClient,
    auth_context: AuthContext,
    *,
    internal_code: str = "CA007",
    sku: str = "WM-CA007",
    price: str = "79.90",
    stock_current: int = 20,
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


async def add_item_to_customer_cart(
    client: AsyncClient,
    auth_context: AuthContext,
    *,
    customer_email: str,
    customer_id: uuid.UUID | None = None,
    product_item_id: str,
    quantity: int,
) -> dict:
    auth_context.set_user(role=UserRole.CUSTOMER, email=customer_email, user_id=customer_id)
    response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": product_item_id, "quantity": quantity},
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_pickup_order_with_valid_cart(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    item = await create_catalog_item_for_order(client, auth_context=auth_context)
    await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email="customer1@example.com",
        product_item_id=item["id"],
        quantity=2,
    )

    response = await client.post(
        "/api/v1/orders",
        json={"fulfillment_type": "pickup", "notes": "retirada no balcao"},
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["fulfillment_type"] == "pickup"
    assert payload["order_status"] == "waiting_payment"
    assert payload["payment_status"] == "pending"
    assert payload["address_id"] is None
    assert Decimal(payload["shipping_price"]) == Decimal("0.00")
    assert Decimal(payload["subtotal"]) == Decimal("159.80")
    assert Decimal(payload["total"]) == Decimal("159.80")
    assert payload["items"][0]["internal_code_snapshot"] == "CA007"


@pytest.mark.asyncio
async def test_create_delivery_order_with_valid_address_and_shipping(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await create_shipping_rule(client)
    item = await create_catalog_item_for_order(client, auth_context=auth_context)
    customer = auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")
    address = await create_address(db_session_factory, user_id=customer.id)

    response_add = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 1},
    )
    assert response_add.status_code == 200

    response = await client.post(
        "/api/v1/orders",
        json={"fulfillment_type": "delivery", "address_id": str(address.id)},
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["fulfillment_type"] == "delivery"
    assert payload["address_id"] == str(address.id)
    assert Decimal(payload["shipping_price"]) == Decimal("19.90")
    assert Decimal(payload["subtotal"]) == Decimal("79.90")
    assert Decimal(payload["total"]) == Decimal("99.80")


@pytest.mark.asyncio
async def test_prevent_creating_order_with_empty_cart(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")

    response = await client.post("/api/v1/orders", json={"fulfillment_type": "pickup"})

    assert response.status_code == 400
    assert response.json()["code"] == "business_rule_error"


@pytest.mark.asyncio
async def test_prevent_creating_order_with_insufficient_stock(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    item = await create_catalog_item_for_order(
        client,
        auth_context=auth_context,
        internal_code="CA009",
        sku="WM-CA009",
        stock_current=2,
    )
    await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email="customer1@example.com",
        product_item_id=item["id"],
        quantity=2,
    )

    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    stock_response = await client.patch(
        f"/api/v1/admin/product-items/{item['id']}/stock",
        json={"quantity": 1, "operation": "set", "reason": "ajuste manual"},
    )
    assert stock_response.status_code == 200

    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")
    response = await client.post("/api/v1/orders", json={"fulfillment_type": "pickup"})

    assert response.status_code == 400
    assert response.json()["code"] == "business_rule_error"


@pytest.mark.asyncio
async def test_prevent_using_address_from_another_user(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await create_shipping_rule(client)
    item = await create_catalog_item_for_order(client, auth_context=auth_context)
    customer_id = uuid.uuid4()
    await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email="customer1@example.com",
        customer_id=customer_id,
        product_item_id=item["id"],
        quantity=1,
    )

    other_user_id = uuid.uuid4()
    other_address = await create_address(db_session_factory, user_id=other_user_id)
    auth_context.set_user(
        role=UserRole.CUSTOMER,
        email="customer1@example.com",
        user_id=customer_id,
    )

    response = await client.post(
        "/api/v1/orders",
        json={"fulfillment_type": "delivery", "address_id": str(other_address.id)},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "not_found_error"


@pytest.mark.asyncio
async def test_list_my_orders(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    item = await create_catalog_item_for_order(client, auth_context=auth_context)
    customer_id = uuid.uuid4()
    await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email="customer1@example.com",
        customer_id=customer_id,
        product_item_id=item["id"],
        quantity=1,
    )
    first_order = await client.post("/api/v1/orders", json={"fulfillment_type": "pickup"})
    assert first_order.status_code == 201

    await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email="customer1@example.com",
        customer_id=customer_id,
        product_item_id=item["id"],
        quantity=2,
    )
    second_order = await client.post("/api/v1/orders", json={"fulfillment_type": "pickup"})
    assert second_order.status_code == 201

    response = await client.get("/api/v1/orders/me?page=1&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 2
    assert len(payload["data"]) == 2


@pytest.mark.asyncio
async def test_prevent_user_from_viewing_other_user_order(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    item = await create_catalog_item_for_order(client, auth_context=auth_context)
    await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email="customer1@example.com",
        product_item_id=item["id"],
        quantity=1,
    )
    create_response = await client.post("/api/v1/orders", json={"fulfillment_type": "pickup"})
    order_id = create_response.json()["data"]["id"]

    auth_context.set_user(role=UserRole.CUSTOMER, email="customer2@example.com")
    response = await client.get(f"/api/v1/orders/me/{order_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found_error"


@pytest.mark.asyncio
async def test_admin_can_list_orders(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    item = await create_catalog_item_for_order(client, auth_context=auth_context)
    await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email="customer1@example.com",
        product_item_id=item["id"],
        quantity=1,
    )
    create_response = await client.post("/api/v1/orders", json={"fulfillment_type": "pickup"})
    assert create_response.status_code == 201

    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    response = await client.get("/api/v1/admin/orders?page=1&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert payload["data"][0]["order_status"] == "waiting_payment"


@pytest.mark.asyncio
async def test_cart_is_converted_after_order_creation(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    item = await create_catalog_item_for_order(client, auth_context=auth_context)
    customer_id = uuid.uuid4()
    cart_payload = await add_item_to_customer_cart(
        client,
        auth_context,
        customer_email="customer1@example.com",
        customer_id=customer_id,
        product_item_id=item["id"],
        quantity=1,
    )
    original_cart_id = uuid.UUID(cart_payload["id"])

    create_response = await client.post("/api/v1/orders", json={"fulfillment_type": "pickup"})
    assert create_response.status_code == 201

    async with db_session_factory() as session:
        cart = await session.scalar(select(Cart).where(Cart.id == original_cart_id))
        assert cart is not None
        assert cart.status == CartStatus.CONVERTED

    new_cart_response = await client.get("/api/v1/cart")
    assert new_cart_response.status_code == 200
    new_cart = new_cart_response.json()["data"]
    assert new_cart["status"] == "active"
    assert new_cart["items"] == []
    assert new_cart["id"] != original_cart_id


@pytest.mark.asyncio
async def test_order_total_is_calculated_correctly(
    client: AsyncClient,
    auth_context: AuthContext,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await create_shipping_rule(client)
    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    category = await create_category(client)
    product = await create_product(client, category_id=category["id"])
    item_one = await create_product_item(
        client,
        product_id=product["id"],
        internal_code="CA011",
        sku="WM-CA011",
        price="79.90",
        stock_current=10,
    )
    item_two = await create_product_item(
        client,
        product_id=product["id"],
        internal_code="CA012",
        sku="WM-CA012",
        price="19.90",
        stock_current=10,
    )

    customer = auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")
    address = await create_address(db_session_factory, user_id=customer.id)
    first_add = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item_one["id"], "quantity": 2},
    )
    second_add = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item_two["id"], "quantity": 1},
    )
    assert first_add.status_code == 200
    assert second_add.status_code == 200

    response = await client.post(
        "/api/v1/orders",
        json={"fulfillment_type": "delivery", "address_id": str(address.id)},
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert Decimal(payload["subtotal"]) == Decimal("179.70")
    assert Decimal(payload["shipping_price"]) == Decimal("19.90")
    assert Decimal(payload["discount"]) == Decimal("0.00")
    assert Decimal(payload["total"]) == Decimal("199.60")
