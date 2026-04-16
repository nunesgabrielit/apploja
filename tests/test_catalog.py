from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient


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
    internal_code: str = "CA007",
    sku: str = "WM-CA007",
    stock_current: int = 20,
    stock_minimum: int = 5,
) -> dict:
    response = await client.post(
        "/api/v1/admin/product-items",
        json={
            "product_id": product_id,
            "internal_code": internal_code,
            "sku": sku,
            "name": "Carregador MOTOROLA 16X Turbo",
            "connector_type": "Tipo C",
            "power": "45W",
            "voltage": "220V",
            "short_description": "carregador turbo motorola tipo c",
            "price": "79.90",
            "stock_current": stock_current,
            "stock_minimum": stock_minimum,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/admin/categories",
        json={"name": "Carregadores", "description": "Acessorios de energia"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["name"] == "Carregadores"


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient) -> None:
    category = await create_category(client)

    response = await client.put(
        f"/api/v1/admin/categories/{category['id']}",
        json={"description": "Categoria atualizada"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["description"] == "Categoria atualizada"


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient) -> None:
    category = await create_category(client)

    response = await client.post(
        "/api/v1/admin/products",
        json={
            "category_id": category["id"],
            "name_base": "Carregadores Motorola",
            "brand": "Motorola",
            "description": "Linha Motorola",
            "image_url": "https://example.com/motorola.png",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"]["name_base"] == "Carregadores Motorola"
    assert payload["data"]["category"]["id"] == category["id"]


@pytest.mark.asyncio
async def test_create_product_item(client: AsyncClient) -> None:
    category = await create_category(client)
    product = await create_product(client, category_id=category["id"])

    response = await client.post(
        "/api/v1/admin/product-items",
        json={
            "product_id": product["id"],
            "internal_code": "CA007",
            "sku": "WM-CA007",
            "name": "Carregador MOTOROLA 16X Turbo",
            "connector_type": "Tipo C",
            "power": "45W",
            "voltage": "220V",
            "short_description": "carregador turbo motorola tipo c",
            "price": "79.90",
            "stock_current": 20,
            "stock_minimum": 5,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"]["sku"] == "WM-CA007"
    assert Decimal(payload["data"]["price"]) == Decimal("79.90")


@pytest.mark.asyncio
async def test_prevent_duplicate_sku(client: AsyncClient) -> None:
    category = await create_category(client)
    product = await create_product(client, category_id=category["id"])
    await create_product_item(client, product_id=product["id"], internal_code="CA007", sku="WM-CA007")

    response = await client.post(
        "/api/v1/admin/product-items",
        json={
            "product_id": product["id"],
            "internal_code": "CA008",
            "sku": "WM-CA007",
            "name": "Carregador MOTOROLA 18X Turbo",
            "price": "89.90",
            "stock_current": 10,
            "stock_minimum": 5,
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict_error"


@pytest.mark.asyncio
async def test_prevent_duplicate_internal_code(client: AsyncClient) -> None:
    category = await create_category(client)
    product = await create_product(client, category_id=category["id"])
    await create_product_item(client, product_id=product["id"], internal_code="CA007", sku="WM-CA007")

    response = await client.post(
        "/api/v1/admin/product-items",
        json={
            "product_id": product["id"],
            "internal_code": "CA007",
            "sku": "WM-CA008",
            "name": "Carregador MOTOROLA 18X Turbo",
            "price": "89.90",
            "stock_current": 10,
            "stock_minimum": 5,
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict_error"


@pytest.mark.asyncio
async def test_prevent_negative_stock(client: AsyncClient) -> None:
    category = await create_category(client)
    product = await create_product(client, category_id=category["id"])
    item = await create_product_item(
        client,
        product_id=product["id"],
        internal_code="CA007",
        sku="WM-CA007",
        stock_current=2,
        stock_minimum=1,
    )

    response = await client.patch(
        f"/api/v1/admin/product-items/{item['id']}/stock",
        json={"quantity": 3, "operation": "decrement", "reason": "ajuste"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "business_rule_error"


@pytest.mark.asyncio
async def test_filter_product_items_low_stock(client: AsyncClient) -> None:
    category = await create_category(client)
    product = await create_product(client, category_id=category["id"])
    await create_product_item(
        client,
        product_id=product["id"],
        internal_code="CA007",
        sku="WM-CA007",
        stock_current=3,
        stock_minimum=5,
    )
    await create_product_item(
        client,
        product_id=product["id"],
        internal_code="CA008",
        sku="WM-CA008",
        stock_current=10,
        stock_minimum=5,
    )

    response = await client.get("/api/v1/product-items?low_stock=true&page=1&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 1
    assert payload["data"][0]["sku"] == "WM-CA007"
    assert payload["data"][0]["low_stock"] is True


@pytest.mark.asyncio
async def test_list_products_by_category(client: AsyncClient) -> None:
    category_one = await create_category(client, name="Carregadores")
    category_two = await create_category(client, name="Cabos")

    await create_product(
        client,
        category_id=category_one["id"],
        name_base="Carregadores Motorola",
        brand="Motorola",
    )
    await create_product(
        client,
        category_id=category_two["id"],
        name_base="Cabos HDMI",
        brand="Genérica",
    )

    response = await client.get(
        f"/api/v1/products?category_id={category_one['id']}&page=1&page_size=20"
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 1
    assert payload["data"][0]["name_base"] == "Carregadores Motorola"
