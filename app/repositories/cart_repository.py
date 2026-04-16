from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.enums import CartStatus
from app.models.product import Product
from app.models.product_item import ProductItem


class CartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _cart_load_options(self) -> tuple:
        return (
            selectinload(Cart.items)
            .joinedload(CartItem.product_item)
            .joinedload(ProductItem.product)
            .joinedload(Product.category),
        )

    async def get_active_by_user_id(self, user_id: UUID) -> Cart | None:
        statement = (
            select(Cart)
            .where(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE)
            .options(*self._cart_load_options())
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_active_cart(self, user_id: UUID) -> Cart:
        cart = Cart(user_id=user_id, status=CartStatus.ACTIVE)
        self.session.add(cart)
        await self.session.flush()
        return cart

    async def get_item_by_cart_and_product_item(
        self,
        cart_id: UUID,
        product_item_id: UUID,
    ) -> CartItem | None:
        statement = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id, CartItem.product_item_id == product_item_id)
            .options(joinedload(CartItem.product_item).joinedload(ProductItem.product))
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_item_by_user_and_id(self, user_id: UUID, item_id: UUID) -> CartItem | None:
        statement = (
            select(CartItem)
            .join(CartItem.cart)
            .where(
                Cart.user_id == user_id,
                Cart.status == CartStatus.ACTIVE,
                CartItem.id == item_id,
            )
            .options(joinedload(CartItem.product_item).joinedload(ProductItem.product))
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_item(
        self,
        *,
        cart_id: UUID,
        product_item_id: UUID,
        quantity: int,
        unit_price: Decimal,
    ) -> CartItem:
        cart_item = CartItem(
            cart_id=cart_id,
            product_item_id=product_item_id,
            quantity=quantity,
            unit_price=unit_price,
        )
        self.session.add(cart_item)
        await self.session.flush()
        return cart_item

    async def delete_item(self, cart_item: CartItem) -> None:
        await self.session.delete(cart_item)
