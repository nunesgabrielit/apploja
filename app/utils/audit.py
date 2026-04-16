from __future__ import annotations

import json
from enum import Enum
from logging import getLogger
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository

logger = getLogger("app.audit")


class AuditAction(str, Enum):
    ADDRESS_CREATED = "address_created"
    ADDRESS_UPDATED = "address_updated"
    ADDRESS_DELETED = "address_deleted"
    CATEGORY_CREATED = "category_created"
    CATEGORY_UPDATED = "category_updated"
    CATEGORY_DELETED = "category_deleted"
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    PRODUCT_ITEM_CREATED = "product_item_created"
    PRODUCT_ITEM_UPDATED = "product_item_updated"
    PRODUCT_ITEM_STOCK_UPDATED = "product_item_stock_updated"
    PRODUCT_ITEM_PRICE_UPDATED = "product_item_price_updated"
    PRODUCT_ITEM_DELETED = "product_item_deleted"
    SHIPPING_RULE_CREATED = "shipping_rule_created"
    SHIPPING_RULE_UPDATED = "shipping_rule_updated"
    SHIPPING_RULE_DELETED = "shipping_rule_deleted"
    ORDER_CREATED = "order_created"
    ORDER_ASSIGNED_EMPLOYEE = "order_assigned_employee"
    ORDER_STATUS_CHANGED = "order_status_changed"
    ORDER_CANCELLED = "order_cancelled"
    PAYMENT_CREATED = "payment_created"
    PAYMENT_APPROVED = "payment_approved"
    PAYMENT_REJECTED = "payment_rejected"
    PAYMENT_CANCELLED = "payment_cancelled"
    PAYMENT_WEBHOOK_DUPLICATE = "payment_webhook_duplicate"
    PAYMENT_STOCK_CONFIRMATION_ERROR = "payment_stock_confirmation_error"


def log_admin_audit(
    *,
    action: AuditAction,
    actor: User | None,
    entity: str,
    entity_id: UUID,
    details: dict[str, Any] | None = None,
) -> None:
    payload = {
        "action": action.value,
        "actor_id": str(actor.id) if actor is not None else None,
        "actor_email": actor.email if actor is not None else "system",
        "actor_role": actor.role.value if actor is not None else "system",
        "entity": entity,
        "entity_id": str(entity_id),
        "details": details or {},
    }
    logger.info("admin_audit %s", json.dumps(payload, default=str, ensure_ascii=True, sort_keys=True))


async def register_audit_event(
    session: AsyncSession,
    *,
    action: AuditAction,
    actor: User | None,
    entity: str,
    entity_id: UUID,
    metadata: dict[str, Any] | None = None,
) -> None:
    await AuditLogRepository(session).create(
        user_id=actor.id if actor is not None else None,
        action=action.value,
        entity=entity,
        entity_id=entity_id,
        metadata=metadata or {},
    )
    log_admin_audit(
        action=action,
        actor=actor,
        entity=entity,
        entity_id=entity_id,
        details=metadata,
    )
