from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.user import User
from app.repositories.cart_repository import CartRepository
from app.repositories.product_item_repository import ProductItemRepository
from app.schemas.cart import CartItemCreate, CartItemUpdate


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.cart_repository = CartRepository(session)
        self.product_item_repository = ProductItemRepository(session)

    async def get_or_create_active_cart(self, user: User) -> Cart:
        cart = await self.cart_repository.get_active_by_user_id(user.id)
        if cart is not None:
            return cart

        try:
            await self.cart_repository.create_active_cart(user.id)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            cart = await self.cart_repository.get_active_by_user_id(user.id)
            if cart is not None:
                return cart
            raise ConflictError("Could not create active cart") from exc

        cart = await self.cart_repository.get_active_by_user_id(user.id)
        if cart is None:
            raise NotFoundError("Active cart not found")
        return cart

    async def add_item(self, user: User, payload: CartItemCreate) -> Cart:
        cart = await self.get_or_create_active_cart(user)
        product_item = await self._get_available_product_item(payload.product_item_id)

        existing_item = await self.cart_repository.get_item_by_cart_and_product_item(
            cart.id,
            product_item.id,
        )

        if existing_item is not None:
            new_quantity = existing_item.quantity + payload.quantity
            self._validate_stock(product_item.stock_current, new_quantity)
            existing_item.quantity = new_quantity
        else:
            self._validate_stock(product_item.stock_current, payload.quantity)
            await self.cart_repository.create_item(
                cart_id=cart.id,
                product_item_id=product_item.id,
                quantity=payload.quantity,
                unit_price=product_item.price,
            )

        await self.session.commit()
        return await self.get_or_create_active_cart(user)

    async def update_item(self, user: User, item_id: UUID, payload: CartItemUpdate) -> Cart:
        cart_item = await self._get_cart_item_for_user(user.id, item_id)
        product_item = await self._get_available_product_item(cart_item.product_item_id)
        self._validate_stock(product_item.stock_current, payload.quantity)

        cart_item.quantity = payload.quantity
        await self.session.commit()
        return await self.get_or_create_active_cart(user)

    async def remove_item(self, user: User, item_id: UUID) -> Cart:
        cart_item = await self._get_cart_item_for_user(user.id, item_id)
        await self.cart_repository.delete_item(cart_item)
        await self.session.commit()
        return await self.get_or_create_active_cart(user)

    async def _get_available_product_item(self, product_item_id: UUID):
        product_item = await self.product_item_repository.get_by_id(product_item_id)
        if product_item is None:
            raise NotFoundError("Product item not found")

        if not product_item.is_active or not product_item.product.is_active:
            raise BusinessRuleError("Product item is not available")

        if product_item.product.category is not None and not product_item.product.category.is_active:
            raise BusinessRuleError("Product item is not available")

        if product_item.stock_current <= 0:
            raise BusinessRuleError("Product item is out of stock")

        return product_item

    async def _get_cart_item_for_user(self, user_id: UUID, item_id: UUID) -> CartItem:
        cart_item = await self.cart_repository.get_item_by_user_and_id(user_id, item_id)
        if cart_item is None:
            raise NotFoundError("Cart item not found")
        return cart_item

    def _validate_stock(self, available_stock: int, requested_quantity: int) -> None:
        if requested_quantity < 1:
            raise BusinessRuleError("Quantity must be at least 1")
        if requested_quantity > available_stock:
            raise BusinessRuleError("Requested quantity exceeds available stock")
