from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class TransactionBase(BaseModel):
    amount: float
    currency: str = "RUB"
    amount_rub: float | None = None
    description: str | None = None
    category_id: UUID

    model_config = STRICT

    @field_validator("category_id", mode="before")
    def _validate_category(cls, v):
        return UUID(str(v))


class TransactionCreate(TransactionBase):
    created_at: datetime | None = None

    model_config = STRICT

    @field_validator("created_at", mode="before")
    def _parse_created_at(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        return datetime.fromisoformat(str(v))


class TransactionUpdate(BaseModel):
    amount: float | None = None
    currency: str | None = None
    description: str | None = None
    category_id: UUID | None = None
    created_at: datetime | None = None

    model_config = STRICT


class Transaction(TransactionBase):
    id: UUID
    created_at: datetime
    amount_rub: float
    account_id: UUID
    user_id: UUID

    model_config = ORM_STRICT
