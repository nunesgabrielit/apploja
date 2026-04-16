from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.address import Address
from app.models.user import User
from app.repositories.address_repository import AddressRepository
from app.schemas.address import AddressCreate, AddressUpdate
from app.services.geocoding_service import GeocodingService
from app.utils.audit import AuditAction, register_audit_event


class AddressService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.address_repository = AddressRepository(session)
        self.geocoding_service = GeocodingService()

    async def list_my_addresses(self, user: User) -> list[Address]:
        return await self.address_repository.list_by_user_id(user.id)

    async def create_for_user(self, user: User, payload: AddressCreate) -> Address:
        normalized_zip_code = self._normalize_zip_code(payload.zip_code)
        coordinates = await self.geocoding_service.geocode_address(
            street=payload.street.strip(),
            number=payload.number.strip(),
            district=payload.district.strip(),
            city=payload.city.strip(),
            state=payload.state.strip().upper(),
            zip_code=normalized_zip_code,
        )
        address = await self.address_repository.create(
            user_id=user.id,
            recipient_name=payload.recipient_name.strip(),
            zip_code=normalized_zip_code,
            street=payload.street.strip(),
            number=payload.number.strip(),
            district=payload.district.strip(),
            city=payload.city.strip(),
            state=payload.state.strip().upper(),
            complement=payload.complement.strip() if payload.complement else None,
            latitude=coordinates[0] if coordinates is not None else None,
            longitude=coordinates[1] if coordinates is not None else None,
        )
        await register_audit_event(
            self.session,
            action=AuditAction.ADDRESS_CREATED,
            actor=user,
            entity="address",
            entity_id=address.id,
            metadata={"zip_code": address.zip_code, "city": address.city, "state": address.state},
        )
        await self.session.commit()
        return await self._get_user_address(user.id, address.id)

    async def update_for_user(self, user: User, address_id: UUID, payload: AddressUpdate) -> Address:
        address = await self._get_user_address(user.id, address_id)

        if payload.recipient_name is not None:
            address.recipient_name = payload.recipient_name.strip()
        if payload.zip_code is not None:
            address.zip_code = self._normalize_zip_code(payload.zip_code)
        if payload.street is not None:
            address.street = payload.street.strip()
        if payload.number is not None:
            address.number = payload.number.strip()
        if payload.district is not None:
            address.district = payload.district.strip()
        if payload.city is not None:
            address.city = payload.city.strip()
        if payload.state is not None:
            address.state = payload.state.strip().upper()
        if payload.complement is not None:
            address.complement = payload.complement.strip() or None
        if payload.is_active is not None:
            address.is_active = payload.is_active

        coordinates = await self.geocoding_service.geocode_address(
            street=address.street,
            number=address.number,
            district=address.district,
            city=address.city,
            state=address.state,
            zip_code=address.zip_code,
        )
        address.latitude = coordinates[0] if coordinates is not None else None
        address.longitude = coordinates[1] if coordinates is not None else None

        await register_audit_event(
            self.session,
            action=AuditAction.ADDRESS_UPDATED,
            actor=user,
            entity="address",
            entity_id=address.id,
            metadata={"zip_code": address.zip_code, "city": address.city, "state": address.state},
        )
        await self.session.commit()
        return await self._get_user_address(user.id, address.id)

    async def deactivate_for_user(self, user: User, address_id: UUID) -> Address:
        address = await self._get_user_address(user.id, address_id)
        address.is_active = False
        await register_audit_event(
            self.session,
            action=AuditAction.ADDRESS_DELETED,
            actor=user,
            entity="address",
            entity_id=address.id,
            metadata={"zip_code": address.zip_code, "city": address.city, "state": address.state},
        )
        await self.session.commit()
        return await self._get_user_address(user.id, address.id)

    async def _get_user_address(self, user_id: UUID, address_id: UUID) -> Address:
        address = await self.address_repository.get_by_user_and_id(user_id, address_id)
        if address is None:
            raise NotFoundError("Address not found")
        return address

    @staticmethod
    def _normalize_zip_code(value: str) -> str:
        normalized = re.sub(r"\D", "", value)
        if len(normalized) != 8:
            raise BusinessRuleError("ZIP code must contain exactly 8 digits")
        return normalized
