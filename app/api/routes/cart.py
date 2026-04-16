from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentCustomerDep, DBSession
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse
from app.schemas.common import ApiResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=ApiResponse[CartResponse])
async def get_cart(
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[CartResponse]:
    cart = await CartService(session).get_or_create_active_cart(current_user)
    return ApiResponse[CartResponse](
        message="Cart retrieved successfully",
        data=CartResponse.from_model(cart),
    )


@router.post("/items", response_model=ApiResponse[CartResponse])
async def add_cart_item(
    payload: CartItemCreate,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[CartResponse]:
    cart = await CartService(session).add_item(current_user, payload)
    return ApiResponse[CartResponse](
        message="Cart item added successfully",
        data=CartResponse.from_model(cart),
    )


@router.put("/items/{item_id}", response_model=ApiResponse[CartResponse])
async def update_cart_item(
    item_id: UUID,
    payload: CartItemUpdate,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[CartResponse]:
    cart = await CartService(session).update_item(current_user, item_id, payload)
    return ApiResponse[CartResponse](
        message="Cart item updated successfully",
        data=CartResponse.from_model(cart),
    )


@router.delete("/items/{item_id}", response_model=ApiResponse[CartResponse])
async def remove_cart_item(
    item_id: UUID,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[CartResponse]:
    cart = await CartService(session).remove_item(current_user, item_id)
    return ApiResponse[CartResponse](
        message="Cart item removed successfully",
        data=CartResponse.from_model(cart),
    )
