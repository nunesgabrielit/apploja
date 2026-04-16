from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.strip().lower())
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        email: str,
        phone: str | None,
        password_hash: str,
        role: UserRole,
    ) -> User:
        user = User(
            name=name,
            email=email.strip().lower(),
            phone=phone,
            password_hash=password_hash,
            role=role,
        )
        self.session.add(user)
        await self.session.flush()
        return user
