from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import StockMovementSource, StockMovementType


class StockMovementResponse(BaseModel):
    id: UUID
    product_item_id: UUID
    movement_type: StockMovementType
    quantity: int
    source: StockMovementSource
    reference_id: UUID | None
    performed_by_user_id: UUID | None
    created_at: datetime

    @classmethod
    def from_model(cls, movement: object) -> "StockMovementResponse":
        return cls(
            id=movement.id,
            product_item_id=movement.product_item_id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            source=movement.source,
            reference_id=movement.reference_id,
            performed_by_user_id=movement.performed_by_user_id,
            created_at=movement.created_at,
        )
