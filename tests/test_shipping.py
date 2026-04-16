from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient


async def create_shipping_rule(
    client: AsyncClient,
    *,
    zip_code_start: str = "69900000",
    zip_code_end: str = "69900999",
    rule_name: str = "Centro Rio Branco",
    shipping_price: str = "19.90",
    estimated_time_text: str = "2 dias uteis",
) -> dict:
    response = await client.post(
        "/api/v1/admin/shipping-rules",
        json={
            "zip_code_start": zip_code_start,
            "zip_code_end": zip_code_end,
            "rule_name": rule_name,
            "shipping_price": shipping_price,
            "estimated_time_text": estimated_time_text,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_shipping_rule(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/admin/shipping-rules",
        json={
            "zip_code_start": "69900-000",
            "zip_code_end": "69900-999",
            "rule_name": "Centro Rio Branco",
            "shipping_price": "19.90",
            "estimated_time_text": "2 dias uteis",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["zip_code_start"] == "69900000"
    assert payload["zip_code_end"] == "69900999"
    assert Decimal(payload["shipping_price"]) == Decimal("19.90")


@pytest.mark.asyncio
async def test_prevent_invalid_shipping_range(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/admin/shipping-rules",
        json={
            "zip_code_start": "69901999",
            "zip_code_end": "69901000",
            "rule_name": "Faixa invalida",
            "shipping_price": "10.00",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "business_rule_error"


@pytest.mark.asyncio
async def test_calculate_shipping_with_covered_zip_code(client: AsyncClient) -> None:
    await create_shipping_rule(client)

    response = await client.post(
        "/api/v1/shipping/calculate",
        json={"zip_code": "69900050", "fulfillment_type": "delivery"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["zip_code_normalized"] == "69900050"
    assert payload["rule_name"] == "Centro Rio Branco"
    assert Decimal(payload["shipping_price"]) == Decimal("19.90")
    assert payload["covered"] is True


@pytest.mark.asyncio
async def test_return_error_when_zip_code_is_not_covered(client: AsyncClient) -> None:
    await create_shipping_rule(client)

    response = await client.post(
        "/api/v1/shipping/calculate",
        json={"zip_code": "70000000", "fulfillment_type": "delivery"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "not_found_error"


@pytest.mark.asyncio
async def test_normalize_zip_code_with_hyphen(client: AsyncClient) -> None:
    await create_shipping_rule(client)

    response = await client.post(
        "/api/v1/shipping/calculate",
        json={"zip_code": "69900-050", "fulfillment_type": "delivery"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["zip_code"] == "69900-050"
    assert payload["zip_code_normalized"] == "69900050"


@pytest.mark.asyncio
async def test_pickup_returns_zero_shipping(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/shipping/calculate",
        json={"zip_code": "69900-050", "fulfillment_type": "pickup"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["rule_name"] == "Retirada na loja"
    assert payload["estimated_time_text"] == "Retirada na loja"
    assert Decimal(payload["shipping_price"]) == Decimal("0.00")
    assert payload["covered"] is True


@pytest.mark.asyncio
async def test_soft_delete_prevents_inactive_rule_from_being_used(client: AsyncClient) -> None:
    rule = await create_shipping_rule(client)

    delete_response = await client.delete(f"/api/v1/admin/shipping-rules/{rule['id']}")
    assert delete_response.status_code == 200

    calculate_response = await client.post(
        "/api/v1/shipping/calculate",
        json={"zip_code": "69900050", "fulfillment_type": "delivery"},
    )

    assert calculate_response.status_code == 404
    assert calculate_response.json()["code"] == "not_found_error"


@pytest.mark.asyncio
async def test_list_shipping_rules_admin(client: AsyncClient) -> None:
    await create_shipping_rule(client, zip_code_start="69900000", zip_code_end="69900999")
    await create_shipping_rule(
        client,
        zip_code_start="69901000",
        zip_code_end="69901999",
        rule_name="Segundo Distrito",
        shipping_price="25.00",
    )

    response = await client.get("/api/v1/admin/shipping-rules?page=1&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 2
    assert payload["pagination"]["total"] == 2
    assert {item["rule_name"] for item in payload["data"]} == {
        "Centro Rio Branco",
        "Segundo Distrito",
    }
