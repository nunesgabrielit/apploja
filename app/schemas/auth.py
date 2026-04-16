from uuid import UUID

from pydantic import BaseModel

from app.schemas.user import UserRead


class TokenPayload(BaseModel):
    sub: UUID | None = None
    exp: int | None = None


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
