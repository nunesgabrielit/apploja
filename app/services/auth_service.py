from logging import getLogger

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AccessTokenResponse
from app.schemas.user import UserRead, UserRegister

logger = getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)

    async def register_customer(self, payload: UserRegister) -> User:
        existing_user = await self.user_repository.get_by_email(payload.email)
        if existing_user is not None:
            raise ConflictError("A user with this email already exists")

        try:
            user = await self.user_repository.create(
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                password_hash=get_password_hash(payload.password),
                role=UserRole.CUSTOMER,
            )
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError("A user with this email already exists")

        await self.session.refresh(user)
        logger.info("New customer registered: %s", user.email)
        return user

    async def login(self, email: str, password: str) -> AccessTokenResponse:
        user = await self.user_repository.get_by_email(email.strip().lower())

        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Inactive users cannot authenticate")

        access_token = create_access_token(subject=str(user.id))
        return AccessTokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserRead.model_validate(user),
        )
