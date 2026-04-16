from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID | None,
        action: str,
        entity: str,
        entity_id: UUID,
        metadata: dict[str, Any] | None,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            metadata_json=metadata,
        )
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log
