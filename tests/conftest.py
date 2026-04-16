from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db_session
from app.core.dependencies import get_current_user
from app.main import app
from app.models import Base
from app.models.enums import UserRole
from app.models.user import User


def build_user(
    *,
    role: UserRole,
    email: str,
    user_id: uuid.UUID | None = None,
    name: str | None = None,
) -> User:
    resolved_name = name or email.split("@", maxsplit=1)[0].replace(".", " ").title()
    return User(
        id=user_id or uuid.uuid4(),
        name=resolved_name,
        email=email,
        phone="69999999999",
        password_hash="not-used",
        role=role,
        is_active=True,
    )


@dataclass
class AuthContext:
    current_user: User

    def set_user(
        self,
        *,
        role: UserRole,
        email: str,
        user_id: uuid.UUID | None = None,
        name: str | None = None,
    ) -> User:
        self.current_user = build_user(
            role=role,
            email=email,
            user_id=user_id,
            name=name,
        )
        return self.current_user


@pytest.fixture
def auth_context() -> AuthContext:
    return AuthContext(current_user=build_user(role=UserRole.ADMIN, email="admin@example.com"))


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "catalog_test.db"


@pytest.fixture
async def db_session_factory(database_path: Path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}", future=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield session_factory

    await engine.dispose()


@pytest.fixture
async def client(
    db_session_factory: async_sessionmaker[AsyncSession],
    auth_context: AuthContext,
) -> AsyncIterator[AsyncClient]:
    session_factory = db_session_factory

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def override_get_current_user() -> User:
        return auth_context.current_user

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()
