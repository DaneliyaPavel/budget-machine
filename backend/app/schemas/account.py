from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator
from ..models import AccountType

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(
    from_attributes=True, strict=True, json_encoders={AccountType: lambda v: v.value}
)


class AccountBase(BaseModel):
    name: str
    currency_code: str = "RUB"
    type: str = "cash"
    user_id: UUID | None = None

    model_config = STRICT

    @field_validator("type", mode="before")
    def _validate_type(cls, v):
        return v.value if isinstance(v, AccountType) else v


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = None
    currency_code: str | None = None
    type: str | None = None
    user_id: UUID | None = None

    model_config = STRICT

    @field_validator("type", mode="before")
    def _validate_type(cls, v):
        return v.value if isinstance(v, AccountType) else v


class Account(AccountBase):
    id: UUID

    model_config = ORM_STRICT

    @field_validator("id", mode="before")
    def _validate_id(cls, v):
        return UUID(str(v))
