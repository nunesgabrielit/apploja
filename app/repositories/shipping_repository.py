from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping import ShippingDistanceRule, ShippingRule, ShippingStoreConfig
from app.schemas.common import PaginationParams
from app.schemas.shipping import ShippingRuleListFilters


class ShippingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, rule_id: UUID) -> ShippingRule | None:
        return await self.session.get(ShippingRule, rule_id)

    async def list_rules(
        self,
        filters: ShippingRuleListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[ShippingRule], int]:
        conditions = []
        if filters.is_active is not None:
            conditions.append(ShippingRule.is_active.is_(filters.is_active))

        total_statement = select(func.count(ShippingRule.id)).where(*conditions)
        total = await self.session.scalar(total_statement)

        statement = (
            select(ShippingRule)
            .where(*conditions)
            .order_by(ShippingRule.zip_code_start.asc(), ShippingRule.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all()), int(total or 0)

    async def find_matching_active_rule(self, normalized_zip_code: str) -> ShippingRule | None:
        statement = (
            select(ShippingRule)
            .where(
                ShippingRule.is_active.is_(True),
                ShippingRule.zip_code_start <= normalized_zip_code,
                ShippingRule.zip_code_end >= normalized_zip_code,
            )
            .order_by(ShippingRule.zip_code_start.asc(), ShippingRule.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def find_overlapping_active_rule(
        self,
        *,
        zip_code_start: str,
        zip_code_end: str,
        exclude_id: UUID | None = None,
    ) -> ShippingRule | None:
        statement = select(ShippingRule).where(
            ShippingRule.is_active.is_(True),
            ShippingRule.zip_code_start <= zip_code_end,
            ShippingRule.zip_code_end >= zip_code_start,
        )
        if exclude_id is not None:
            statement = statement.where(ShippingRule.id != exclude_id)

        statement = statement.order_by(ShippingRule.zip_code_start.asc()).limit(1)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        zip_code_start: str,
        zip_code_end: str,
        rule_name: str,
        shipping_price,
        estimated_time_text: str | None,
    ) -> ShippingRule:
        rule = ShippingRule(
            zip_code_start=zip_code_start,
            zip_code_end=zip_code_end,
            rule_name=rule_name.strip(),
            shipping_price=shipping_price,
            estimated_time_text=estimated_time_text,
        )
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def list_distance_rules(self) -> list[ShippingDistanceRule]:
        statement = (
            select(ShippingDistanceRule)
            .order_by(
                ShippingDistanceRule.is_active.desc(),
                ShippingDistanceRule.sort_order.asc(),
                ShippingDistanceRule.max_distance_km.asc(),
            )
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_active_distance_rules(self) -> list[ShippingDistanceRule]:
        statement = (
            select(ShippingDistanceRule)
            .where(ShippingDistanceRule.is_active.is_(True))
            .order_by(ShippingDistanceRule.sort_order.asc(), ShippingDistanceRule.max_distance_km.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_distance_rule_by_id(self, rule_id: UUID) -> ShippingDistanceRule | None:
        return await self.session.get(ShippingDistanceRule, rule_id)

    async def create_distance_rule(
        self,
        *,
        rule_name: str,
        max_distance_km,
        shipping_price,
        estimated_time_text: str | None,
        sort_order: int,
    ) -> ShippingDistanceRule:
        rule = ShippingDistanceRule(
            rule_name=rule_name.strip(),
            max_distance_km=max_distance_km,
            shipping_price=shipping_price,
            estimated_time_text=estimated_time_text,
            sort_order=sort_order,
        )
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def get_store_config(self) -> ShippingStoreConfig | None:
        statement = (
            select(ShippingStoreConfig)
            .where(ShippingStoreConfig.is_active.is_(True))
            .order_by(ShippingStoreConfig.updated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_store_config(
        self,
        *,
        store_name: str,
        zip_code: str,
        street: str,
        number: str,
        district: str,
        city: str,
        state: str,
        complement: str | None,
        latitude,
        longitude,
    ) -> ShippingStoreConfig:
        config = ShippingStoreConfig(
            store_name=store_name,
            zip_code=zip_code,
            street=street,
            number=number,
            district=district,
            city=city,
            state=state,
            complement=complement,
            latitude=latitude,
            longitude=longitude,
        )
        self.session.add(config)
        await self.session.flush()
        return config
