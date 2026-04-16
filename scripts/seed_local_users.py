from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.user import User

LOCAL_USERS = [
    {
        "name": "Admin WM",
        "email": "admin@wmdistribuidora.com",
        "role": UserRole.ADMIN,
        "password": "Admin@123456",
    },
    {
        "name": "Funcionario WM",
        "email": "funcionario@wmdistribuidora.com",
        "role": UserRole.EMPLOYEE,
        "password": "Funcionario@123456",
    },
    {
        "name": "Cliente WM",
        "email": "cliente@wmdistribuidora.com",
        "role": UserRole.CUSTOMER,
        "password": "Cliente@123456",
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        for user_data in LOCAL_USERS:
            existing = await session.scalar(select(User).where(User.email == user_data["email"]))
            if existing is not None:
                continue

            session.add(
                User(
                    name=user_data["name"],
                    email=user_data["email"],
                    phone="69999999999",
                    password_hash=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    is_active=True,
                )
            )

        await session.commit()

        rows = await session.execute(select(User.email, User.role).order_by(User.email))
        for row in rows:
            print(row)


if __name__ == "__main__":
    asyncio.run(main())
