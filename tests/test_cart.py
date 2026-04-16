from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.enums import UserRole
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


async def create_catalog_item_for_cart(
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


@pytest.mark.asyncio
async def test_get_empty_cart_creates_active_cart(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")

    response = await client.get("/api/v1/cart")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "active"
    assert payload["items"] == []
    assert payload["total_items"] == 0
    assert Decimal(payload["subtotal"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_add_item_to_cart(client: AsyncClient, auth_context: AuthContext) -> None:
    item = await create_catalog_item_for_cart(client, auth_context=auth_context)
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")

    response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 2},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total_items"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["sku"] == "WM-CA007"
    assert payload["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_add_same_item_sums_quantity(client: AsyncClient, auth_context: AuthContext) -> None:
    item = await create_catalog_item_for_cart(client, auth_context=auth_context, stock_current=10)
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")

    first = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 2},
    )
    second = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 3},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    payload = second.json()["data"]
    assert len(payload["items"]) == 1
    assert payload["items"][0]["quantity"] == 5
    assert payload["total_items"] == 5


@pytest.mark.asyncio
async def test_prevent_adding_above_stock(client: AsyncClient, auth_context: AuthContext) -> None:
    item = await create_catalog_item_for_cart(client, auth_context=auth_context, stock_current=2)
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")

    response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 3},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "business_rule_error"


@pytest.mark.asyncio
async def test_update_quantity(client: AsyncClient, auth_context: AuthContext) -> None:
    item = await create_catalog_item_for_cart(client, auth_context=auth_context, stock_current=10)
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")
    add_response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 2},
    )
    cart_item_id = add_response.json()["data"]["items"][0]["id"]

    response = await client.put(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": 4},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["items"][0]["quantity"] == 4
    assert payload["total_items"] == 4


@pytest.mark.asyncio
async def test_prevent_invalid_quantity_update(client: AsyncClient, auth_context: AuthContext) -> None:
    item = await create_catalog_item_for_cart(client, auth_context=auth_context, stock_current=10)
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")
    add_response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 2},
    )
    cart_item_id = add_response.json()["data"]["items"][0]["id"]

    response = await client.put(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": 0},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


@pytest.mark.asyncio
async def test_remove_item_from_cart(client: AsyncClient, auth_context: AuthContext) -> None:
    item = await create_catalog_item_for_cart(client, auth_context=auth_context)
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")
    add_response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 2},
    )
    cart_item_id = add_response.json()["data"]["items"][0]["id"]

    response = await client.delete(f"/api/v1/cart/items/{cart_item_id}")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["items"] == []
    assert payload["total_items"] == 0
    assert Decimal(payload["subtotal"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_prevent_accessing_other_user_cart_item(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    item = await create_catalog_item_for_cart(client, auth_context=auth_context)
    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")
    add_response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item["id"], "quantity": 2},
    )
    cart_item_id = add_response.json()["data"]["items"][0]["id"]

    auth_context.set_user(role=UserRole.CUSTOMER, email="customer2@example.com")
    response = await client.put(
        f"/api/v1/cart/items/{cart_item_id}",
        json={"quantity": 1},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "not_found_error"


@pytest.mark.asyncio
async def test_cart_subtotal_is_calculated_correctly(
    client: AsyncClient,
    auth_context: AuthContext,
) -> None:
    auth_context.set_user(role=UserRole.ADMIN, email="admin@example.com")
    category = await create_category(client)
    product = await create_product(client, category_id=category["id"])
    item_one = await create_product_item(
        client,
        product_id=product["id"],
        internal_code="CA007",
        sku="WM-CA007",
        price="79.90",
        stock_current=10,
    )
    item_two = await create_product_item(
        client,
        product_id=product["id"],
        internal_code="CA008",
        sku="WM-CA008",
        price="19.90",
        stock_current=10,
    )

    auth_context.set_user(role=UserRole.CUSTOMER, email="customer1@example.com")
    await client.post("/api/v1/cart/items", json={"product_item_id": item_one["id"], "quantity": 2})
    response = await client.post(
        "/api/v1/cart/items",
        json={"product_item_id": item_two["id"], "quantity": 1},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert Decimal(payload["subtotal"]) == Decimal("179.70")
    assert payload["total_items"] == 3
