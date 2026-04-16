from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.address import Address
from app.models.enums import FulfillmentType
from app.models.shipping import ShippingDistanceRule, ShippingRule, ShippingStoreConfig
from app.models.user import User
from app.repositories.address_repository import AddressRepository
from app.repositories.shipping_repository import ShippingRepository
from app.schemas.common import PaginationParams
from app.schemas.shipping import (
    ShippingCalculateRequest,
    ShippingCalculateResponse,
    ShippingDistanceRuleCreate,
    ShippingDistanceRuleUpdate,
    ShippingRuleCreate,
    ShippingRuleListFilters,
    ShippingRuleUpdate,
    ShippingStoreConfigUpsert,
)
from app.services.geocoding_service import GeocodingService
from app.utils.audit import AuditAction, log_admin_audit


class ShippingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.address_repository = AddressRepository(session)
        self.geocoding_service = GeocodingService()
        self.shipping_repository = ShippingRepository(session)

    async def list_rules(
        self,
        filters: ShippingRuleListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[ShippingRule], int]:
        return await self.shipping_repository.list_rules(filters, pagination)

    async def list_distance_rules(self) -> list[ShippingDistanceRule]:
        return await self.shipping_repository.list_distance_rules()

    async def get_store_config(self) -> ShippingStoreConfig | None:
        return await self.shipping_repository.get_store_config()

    async def calculate(
        self,
        payload: ShippingCalculateRequest,
    ) -> ShippingCalculateResponse:
        if payload.fulfillment_type == FulfillmentType.PICKUP:
            return ShippingCalculateResponse(
                zip_code=payload.zip_code,
                zip_code_normalized=None,
                fulfillment_type=payload.fulfillment_type,
                shipping_price=Decimal("0.00"),
                estimated_time_text="Retirada na loja",
                rule_name="Retirada na loja",
                covered=True,
                calculation_mode="pickup",
                distance_km=None,
            )

        if payload.address_id is not None:
            distance_result = await self._calculate_by_distance(payload.address_id)
            if distance_result is not None:
                return distance_result

        normalized_zip_code = self._normalize_zip_code(payload.zip_code)
        rule = await self.shipping_repository.find_matching_active_rule(normalized_zip_code)
        if rule is None:
            raise NotFoundError("No active shipping rule covers the provided ZIP code")

        return ShippingCalculateResponse(
            zip_code=payload.zip_code,
            zip_code_normalized=normalized_zip_code,
            fulfillment_type=payload.fulfillment_type,
            shipping_price=rule.shipping_price,
            estimated_time_text=rule.estimated_time_text,
            rule_name=rule.rule_name,
            covered=True,
            calculation_mode="zip_code",
            distance_km=None,
        )

    async def create(self, payload: ShippingRuleCreate, actor: User) -> ShippingRule:
        zip_code_start, zip_code_end = self._normalize_range(
            payload.zip_code_start,
            payload.zip_code_end,
        )
        await self._ensure_no_overlap(zip_code_start, zip_code_end)

        rule = await self.shipping_repository.create(
            zip_code_start=zip_code_start,
            zip_code_end=zip_code_end,
            rule_name=payload.rule_name,
            shipping_price=payload.shipping_price,
            estimated_time_text=payload.estimated_time_text,
        )
        await self.session.commit()
        await self.session.refresh(rule)

        log_admin_audit(
            action=AuditAction.SHIPPING_RULE_CREATED,
            actor=actor,
            entity="shipping_rule",
            entity_id=rule.id,
            details={
                "zip_code_start": rule.zip_code_start,
                "zip_code_end": rule.zip_code_end,
                "rule_name": rule.rule_name,
            },
        )
        return rule

    async def update(self, rule_id: UUID, payload: ShippingRuleUpdate, actor: User) -> ShippingRule:
        rule = await self._get_rule(rule_id)
        update_data = payload.model_dump(exclude_unset=True)

        resolved_start = update_data.get("zip_code_start", rule.zip_code_start)
        resolved_end = update_data.get("zip_code_end", rule.zip_code_end)
        normalized_start, normalized_end = self._normalize_range(resolved_start, resolved_end)
        final_is_active = update_data.get("is_active", rule.is_active)

        if final_is_active:
            await self._ensure_no_overlap(normalized_start, normalized_end, exclude_id=rule.id)

        rule.zip_code_start = normalized_start
        rule.zip_code_end = normalized_end

        if "rule_name" in update_data:
            rule.rule_name = payload.rule_name
        if "shipping_price" in update_data:
            rule.shipping_price = payload.shipping_price
        if "estimated_time_text" in update_data:
            rule.estimated_time_text = payload.estimated_time_text
        if "is_active" in update_data:
            rule.is_active = payload.is_active

        await self.session.commit()
        await self.session.refresh(rule)

        log_admin_audit(
            action=AuditAction.SHIPPING_RULE_UPDATED,
            actor=actor,
            entity="shipping_rule",
            entity_id=rule.id,
            details={
                "zip_code_start": rule.zip_code_start,
                "zip_code_end": rule.zip_code_end,
                "rule_name": rule.rule_name,
                "shipping_price": str(rule.shipping_price),
                "is_active": rule.is_active,
            },
        )
        return rule

    async def deactivate(self, rule_id: UUID, actor: User) -> ShippingRule:
        rule = await self._get_rule(rule_id)
        rule.is_active = False
        await self.session.commit()
        await self.session.refresh(rule)

        log_admin_audit(
            action=AuditAction.SHIPPING_RULE_DELETED,
            actor=actor,
            entity="shipping_rule",
            entity_id=rule.id,
            details={"is_active": False},
        )
        return rule

    async def upsert_store_config(
        self,
        payload: ShippingStoreConfigUpsert,
        actor: User,
    ) -> ShippingStoreConfig:
        existing_config = await self.shipping_repository.get_store_config()
        normalized_zip_code = self._normalize_zip_code(payload.zip_code)
        coordinates = await self.geocoding_service.geocode_address(
            street=payload.street.strip(),
            number=payload.number.strip(),
            district=payload.district.strip(),
            city=payload.city.strip(),
            state=payload.state.strip().upper(),
            zip_code=normalized_zip_code,
        )

        latitude = coordinates[0] if coordinates is not None else None
        longitude = coordinates[1] if coordinates is not None else None

        if existing_config is None:
            config = await self.shipping_repository.create_store_config(
                store_name=payload.store_name.strip(),
                zip_code=normalized_zip_code,
                street=payload.street.strip(),
                number=payload.number.strip(),
                district=payload.district.strip(),
                city=payload.city.strip(),
                state=payload.state.strip().upper(),
                complement=payload.complement.strip() if payload.complement else None,
                latitude=latitude,
                longitude=longitude,
            )
        else:
            config = existing_config
            config.store_name = payload.store_name.strip()
            config.zip_code = normalized_zip_code
            config.street = payload.street.strip()
            config.number = payload.number.strip()
            config.district = payload.district.strip()
            config.city = payload.city.strip()
            config.state = payload.state.strip().upper()
            config.complement = payload.complement.strip() if payload.complement else None
            config.latitude = latitude
            config.longitude = longitude

        await self.session.commit()
        await self.session.refresh(config)

        log_admin_audit(
            action=AuditAction.SHIPPING_RULE_UPDATED,
            actor=actor,
            entity="shipping_store_config",
            entity_id=config.id,
            details={
                "zip_code": config.zip_code,
                "city": config.city,
                "state": config.state,
            },
        )
        return config

    async def create_distance_rule(
        self,
        payload: ShippingDistanceRuleCreate,
        actor: User,
    ) -> ShippingDistanceRule:
        await self._ensure_distance_rule_uniqueness(payload.max_distance_km)
        rule = await self.shipping_repository.create_distance_rule(
            rule_name=payload.rule_name,
            max_distance_km=payload.max_distance_km,
            shipping_price=payload.shipping_price,
            estimated_time_text=payload.estimated_time_text,
            sort_order=payload.sort_order,
        )
        await self.session.commit()
        await self.session.refresh(rule)

        log_admin_audit(
            action=AuditAction.SHIPPING_RULE_CREATED,
            actor=actor,
            entity="shipping_distance_rule",
            entity_id=rule.id,
            details={
                "max_distance_km": str(rule.max_distance_km),
                "shipping_price": str(rule.shipping_price),
            },
        )
        return rule

    async def update_distance_rule(
        self,
        rule_id: UUID,
        payload: ShippingDistanceRuleUpdate,
        actor: User,
    ) -> ShippingDistanceRule:
        rule = await self._get_distance_rule(rule_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "max_distance_km" in update_data and payload.max_distance_km != rule.max_distance_km:
            await self._ensure_distance_rule_uniqueness(payload.max_distance_km, exclude_id=rule.id)
            rule.max_distance_km = payload.max_distance_km
        if "rule_name" in update_data:
            rule.rule_name = payload.rule_name
        if "shipping_price" in update_data:
            rule.shipping_price = payload.shipping_price
        if "estimated_time_text" in update_data:
            rule.estimated_time_text = payload.estimated_time_text
        if "sort_order" in update_data:
            rule.sort_order = payload.sort_order
        if "is_active" in update_data:
            rule.is_active = payload.is_active

        await self.session.commit()
        await self.session.refresh(rule)

        log_admin_audit(
            action=AuditAction.SHIPPING_RULE_UPDATED,
            actor=actor,
            entity="shipping_distance_rule",
            entity_id=rule.id,
            details={
                "max_distance_km": str(rule.max_distance_km),
                "shipping_price": str(rule.shipping_price),
            },
        )
        return rule

    async def deactivate_distance_rule(self, rule_id: UUID, actor: User) -> ShippingDistanceRule:
        rule = await self._get_distance_rule(rule_id)
        rule.is_active = False
        await self.session.commit()
        await self.session.refresh(rule)

        log_admin_audit(
            action=AuditAction.SHIPPING_RULE_DELETED,
            actor=actor,
            entity="shipping_distance_rule",
            entity_id=rule.id,
            details={"is_active": False},
        )
        return rule

    async def _calculate_by_distance(self, address_id: UUID) -> ShippingCalculateResponse | None:
        store_config = await self.shipping_repository.get_store_config()
        distance_rules = await self.shipping_repository.list_active_distance_rules()
        if store_config is None or not distance_rules:
            return None

        address = await self.address_repository.get_by_id(address_id)
        if address is None or not address.is_active:
            raise NotFoundError("Address not found")

        store_coordinates = await self._ensure_store_coordinates(store_config)
        address_coordinates = await self._ensure_address_coordinates(address)
        if store_coordinates is None or address_coordinates is None:
            return None

        distance_km = self._calculate_haversine_km(
            store_coordinates[0],
            store_coordinates[1],
            address_coordinates[0],
            address_coordinates[1],
        )

        matched_rule = next(
            (rule for rule in distance_rules if distance_km <= rule.max_distance_km),
            None,
        )
        if matched_rule is None:
            raise NotFoundError("The delivery address is outside the coverage radius")

        return ShippingCalculateResponse(
            zip_code=address.zip_code,
            zip_code_normalized=address.zip_code,
            fulfillment_type=FulfillmentType.DELIVERY,
            shipping_price=matched_rule.shipping_price,
            estimated_time_text=matched_rule.estimated_time_text,
            rule_name=matched_rule.rule_name,
            covered=True,
            calculation_mode="distance",
            distance_km=distance_km,
        )

    async def _ensure_store_coordinates(
        self,
        config: ShippingStoreConfig,
    ) -> tuple[Decimal, Decimal] | None:
        if config.latitude is not None and config.longitude is not None:
            return config.latitude, config.longitude

        coordinates = await self.geocoding_service.geocode_address(
            street=config.street,
            number=config.number,
            district=config.district,
            city=config.city,
            state=config.state,
            zip_code=config.zip_code,
        )
        if coordinates is None:
            return None

        config.latitude = coordinates[0]
        config.longitude = coordinates[1]
        await self.session.flush()
        return coordinates

    async def _ensure_address_coordinates(self, address: Address) -> tuple[Decimal, Decimal] | None:
        if address.latitude is not None and address.longitude is not None:
            return address.latitude, address.longitude

        coordinates = await self.geocoding_service.geocode_address(
            street=address.street,
            number=address.number,
            district=address.district,
            city=address.city,
            state=address.state,
            zip_code=address.zip_code,
        )
        if coordinates is None:
            return None

        address.latitude = coordinates[0]
        address.longitude = coordinates[1]
        await self.session.flush()
        return coordinates

    def _calculate_haversine_km(
        self,
        latitude_a: Decimal,
        longitude_a: Decimal,
        latitude_b: Decimal,
        longitude_b: Decimal,
    ) -> Decimal:
        earth_radius_km = 6371.0
        lat1 = math.radians(float(latitude_a))
        lon1 = math.radians(float(longitude_a))
        lat2 = math.radians(float(latitude_b))
        lon2 = math.radians(float(longitude_b))

        diff_lat = lat2 - lat1
        diff_lon = lon2 - lon1

        haversine = (
            math.sin(diff_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(diff_lon / 2) ** 2
        )
        distance = 2 * earth_radius_km * math.asin(math.sqrt(haversine))
        return Decimal(str(distance)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    async def _get_rule(self, rule_id: UUID) -> ShippingRule:
        rule = await self.shipping_repository.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError("Shipping rule not found")
        return rule

    async def _get_distance_rule(self, rule_id: UUID) -> ShippingDistanceRule:
        rule = await self.shipping_repository.get_distance_rule_by_id(rule_id)
        if rule is None:
            raise NotFoundError("Shipping distance rule not found")
        return rule

    async def _ensure_distance_rule_uniqueness(
        self,
        max_distance_km: Decimal,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        rules = await self.shipping_repository.list_distance_rules()
        for rule in rules:
            if exclude_id is not None and rule.id == exclude_id:
                continue
            if rule.max_distance_km == max_distance_km:
                raise ConflictError("A distance rule with this radius already exists")

    async def _ensure_no_overlap(
        self,
        zip_code_start: str,
        zip_code_end: str,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        overlapping_rule = await self.shipping_repository.find_overlapping_active_rule(
            zip_code_start=zip_code_start,
            zip_code_end=zip_code_end,
            exclude_id=exclude_id,
        )
        if overlapping_rule is not None:
            raise ConflictError("An active shipping rule already covers this ZIP code range")

    def _normalize_range(self, zip_code_start: str, zip_code_end: str) -> tuple[str, str]:
        normalized_start = self._normalize_zip_code(zip_code_start)
        normalized_end = self._normalize_zip_code(zip_code_end)

        if normalized_start > normalized_end:
            raise BusinessRuleError("zip_code_start cannot be greater than zip_code_end")

        return normalized_start, normalized_end

    def _normalize_zip_code(self, zip_code: str | None) -> str:
        if zip_code is None:
            raise BusinessRuleError("ZIP code is required for delivery")

        normalized_zip_code = "".join(character for character in zip_code if character.isdigit())
        if len(normalized_zip_code) != 8:
            raise BusinessRuleError("ZIP code must contain exactly 8 digits after normalization")

        return normalized_zip_code
