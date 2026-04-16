from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address


class AddressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, address_id: UUID) -> Address | None:
        return await self.session.get(Address, address_id)

    async def get_by_user_and_id(self, user_id: UUID, address_id: UUID) -> Address | None:
        statement = select(Address).where(Address.id == address_id, Address.user_id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_user_id(self, user_id: UUID) -> list[Address]:
        statement = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_active.desc(), Address.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        user_id: UUID,
        recipient_name: str,
        zip_code: str,
        street: str,
        number: str,
        district: str,
        city: str,
        state: str,
        complement: str | None = None,
        latitude=None,
        longitude=None,
    ) -> Address:
        address = Address(
            user_id=user_id,
            recipient_name=recipient_name,
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
        self.session.add(address)
        await self.session.flush()
        return address
