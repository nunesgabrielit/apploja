from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    token_payload = decode_access_token(token)

    if token_payload.sub is None:
        raise AuthenticationError("Could not validate credentials")

    user_id = UUID(str(token_payload.sub))
    user = await UserRepository(session).get_by_id(user_id)

    if user is None:
        raise AuthenticationError("Could not validate credentials")

    if not user.is_active:
        raise AuthorizationError("Inactive users cannot access this resource")

    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")

    return current_user


async def get_current_employee_or_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role not in {UserRole.ADMIN, UserRole.EMPLOYEE}:
        raise AuthorizationError("Employee or admin access required")

    return current_user


async def get_current_customer(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.CUSTOMER:
        raise AuthorizationError("Customer access required")

    return current_user


DBSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentAdminDep = Annotated[User, Depends(get_current_admin)]
CurrentEmployeeOrAdminDep = Annotated[User, Depends(get_current_employee_or_admin)]
CurrentCustomerDep = Annotated[User, Depends(get_current_customer)]
