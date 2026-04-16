from fastapi import APIRouter

from app.api.routes.addresses import router as addresses_router
from app.api.routes.cart import router as cart_router
from app.api.routes.categories import admin_router as admin_categories_router
from app.api.routes.categories import public_router as categories_router
from app.api.routes.employees import router as admin_employees_router
from app.api.routes.orders import admin_router as admin_orders_router
from app.api.routes.orders import customer_router as orders_router
from app.api.routes.payments import router as payments_router
from app.api.routes.product_items import admin_router as admin_product_items_router
from app.api.routes.product_items import public_router as product_items_router
from app.api.routes.products import admin_router as admin_products_router
from app.api.routes.products import public_router as products_router
from app.api.routes.shipping import admin_router as admin_shipping_rules_router
from app.api.routes.shipping import public_router as shipping_router
from app.api.routes.stock import router as admin_stock_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(addresses_router)
api_router.include_router(cart_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
api_router.include_router(shipping_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(product_items_router)
api_router.include_router(admin_categories_router)
api_router.include_router(admin_orders_router)
api_router.include_router(admin_employees_router)
api_router.include_router(admin_products_router)
api_router.include_router(admin_product_items_router)
api_router.include_router(admin_shipping_rules_router)
api_router.include_router(admin_stock_router)
