from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"
    CUSTOMER = "customer"


class OrderStatus(str, Enum):
    WAITING_PAYMENT = "waiting_payment"
    PAID = "paid"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentProvider(str, Enum):
    MERCADOPAGO = "mercadopago"


class PaymentMethod(str, Enum):
    PIX = "pix"
    CARD = "card"


class FulfillmentType(str, Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"


class CartStatus(str, Enum):
    ACTIVE = "active"
    CONVERTED = "converted"
    ABANDONED = "abandoned"


class StockMovementType(str, Enum):
    SALE = "sale"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    CANCELLATION = "cancellation"
    RETURN = "return"


class StockMovementSource(str, Enum):
    ORDER = "order"
    ADMIN = "admin"
    SYSTEM = "system"
