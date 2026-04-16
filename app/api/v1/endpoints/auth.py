from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import CurrentUserDep, DBSession
from app.schemas.auth import AccessTokenResponse
from app.schemas.user import UserRead, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
async def register_customer(payload: UserRegister, session: DBSession) -> UserRead:
    user = await AuthService(session).register_customer(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=AccessTokenResponse, summary="Authenticate a user")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: DBSession,
) -> AccessTokenResponse:
    return await AuthService(session).login(
        email=form_data.username,
        password=form_data.password,
    )


@router.get("/me", response_model=UserRead, summary="Get current authenticated user")
async def me(current_user: CurrentUserDep) -> UserRead:
    return UserRead.model_validate(current_user)
