from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class UserBase(BaseModel):
    email: str

    model_config = STRICT


class UserCreate(UserBase):
    password: str

    model_config = STRICT


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None

    model_config = STRICT


class JoinAccount(BaseModel):
    account_id: UUID

    model_config = STRICT

    @field_validator("account_id", mode="before")
    def _validate_account(cls, v):
        return UUID(str(v))


class User(UserBase):
    id: UUID
    is_active: bool
    account_id: UUID
    role: str
    created_at: datetime | None = None

    model_config = ORM_STRICT


class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = STRICT


class TokenPair(Token):
    refresh_token: str

    model_config = STRICT


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
    type: str | None = None

    model_config = STRICT


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = STRICT


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = STRICT
