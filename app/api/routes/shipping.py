from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentEmployeeOrAdminDep, DBSession
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.shipping import (
    ShippingCalculateRequest,
    ShippingCalculateResponse,
    ShippingDistanceRuleCreate,
    ShippingDistanceRuleResponse,
    ShippingDistanceRuleUpdate,
    ShippingRuleCreate,
    ShippingRuleListFilters,
    ShippingRuleResponse,
    ShippingRuleUpdate,
    ShippingStoreConfigResponse,
    ShippingStoreConfigUpsert,
)
from app.services.shipping_service import ShippingService

public_router = APIRouter(prefix="/shipping", tags=["shipping"])
admin_router = APIRouter(prefix="/admin/shipping-rules", tags=["admin-shipping-rules"])


@public_router.post("/calculate", response_model=ApiResponse[ShippingCalculateResponse])
async def calculate_shipping(
    payload: ShippingCalculateRequest,
    session: DBSession,
) -> ApiResponse[ShippingCalculateResponse]:
    result = await ShippingService(session).calculate(payload)
    return ApiResponse[ShippingCalculateResponse](
        message="Shipping calculated successfully",
        data=result,
    )


@admin_router.get("", response_model=PaginatedResponse[ShippingRuleResponse])
async def list_shipping_rules(
    filters: Annotated[ShippingRuleListFilters, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> PaginatedResponse[ShippingRuleResponse]:
    rules, total = await ShippingService(session).list_rules(filters, pagination)
    return PaginatedResponse[ShippingRuleResponse](
        message="Shipping rules retrieved successfully",
        data=[ShippingRuleResponse.from_model(rule) for rule in rules],
        pagination=PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        ),
    )


@admin_router.post(
    "",
    response_model=ApiResponse[ShippingRuleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_shipping_rule(
    payload: ShippingRuleCreate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ShippingRuleResponse]:
    rule = await ShippingService(session).create(payload, current_user)
    return ApiResponse[ShippingRuleResponse](
        message="Shipping rule created successfully",
        data=ShippingRuleResponse.from_model(rule),
    )


@admin_router.get("/distance", response_model=ApiResponse[list[ShippingDistanceRuleResponse]])
async def list_distance_rules(
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[list[ShippingDistanceRuleResponse]]:
    rules = await ShippingService(session).list_distance_rules()
    return ApiResponse[list[ShippingDistanceRuleResponse]](
        message="Distance shipping rules retrieved successfully",
        data=[ShippingDistanceRuleResponse.from_model(rule) for rule in rules],
    )


@admin_router.post(
    "/distance",
    response_model=ApiResponse[ShippingDistanceRuleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_distance_rule(
    payload: ShippingDistanceRuleCreate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ShippingDistanceRuleResponse]:
    rule = await ShippingService(session).create_distance_rule(payload, current_user)
    return ApiResponse[ShippingDistanceRuleResponse](
        message="Distance shipping rule created successfully",
        data=ShippingDistanceRuleResponse.from_model(rule),
    )


@admin_router.put("/distance/{rule_id}", response_model=ApiResponse[ShippingDistanceRuleResponse])
async def update_distance_rule(
    rule_id: UUID,
    payload: ShippingDistanceRuleUpdate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ShippingDistanceRuleResponse]:
    rule = await ShippingService(session).update_distance_rule(rule_id, payload, current_user)
    return ApiResponse[ShippingDistanceRuleResponse](
        message="Distance shipping rule updated successfully",
        data=ShippingDistanceRuleResponse.from_model(rule),
    )


@admin_router.delete("/distance/{rule_id}", response_model=ApiResponse[ShippingDistanceRuleResponse])
async def delete_distance_rule(
    rule_id: UUID,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ShippingDistanceRuleResponse]:
    rule = await ShippingService(session).deactivate_distance_rule(rule_id, current_user)
    return ApiResponse[ShippingDistanceRuleResponse](
        message="Distance shipping rule deactivated successfully",
        data=ShippingDistanceRuleResponse.from_model(rule),
    )


@admin_router.get("/store-config", response_model=ApiResponse[ShippingStoreConfigResponse | None])
async def get_store_config(
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ShippingStoreConfigResponse | None]:
    config = await ShippingService(session).get_store_config()
    return ApiResponse[ShippingStoreConfigResponse | None](
        message="Store shipping config retrieved successfully",
        data=ShippingStoreConfigResponse.from_model(config) if config is not None else None,
    )


@admin_router.put("/store-config", response_model=ApiResponse[ShippingStoreConfigResponse])
async def upsert_store_config(
    payload: ShippingStoreConfigUpsert,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ShippingStoreConfigResponse]:
    config = await ShippingService(session).upsert_store_config(payload, current_user)
    return ApiResponse[ShippingStoreConfigResponse](
        message="Store shipping config saved successfully",
        data=ShippingStoreConfigResponse.from_model(config),
    )


@admin_router.put("/{rule_id}", response_model=ApiResponse[ShippingRuleResponse])
async def update_shipping_rule(
    rule_id: UUID,
    payload: ShippingRuleUpdate,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ShippingRuleResponse]:
    rule = await ShippingService(session).update(rule_id, payload, current_user)
    return ApiResponse[ShippingRuleResponse](
        message="Shipping rule updated successfully",
        data=ShippingRuleResponse.from_model(rule),
    )


@admin_router.delete("/{rule_id}", response_model=ApiResponse[ShippingRuleResponse])
async def delete_shipping_rule(
    rule_id: UUID,
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[ShippingRuleResponse]:
    rule = await ShippingService(session).deactivate(rule_id, current_user)
    return ApiResponse[ShippingRuleResponse](
        message="Shipping rule deactivated successfully",
        data=ShippingRuleResponse.from_model(rule),
    )
