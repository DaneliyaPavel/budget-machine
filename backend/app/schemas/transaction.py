from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .posting import PostingCreate

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class TransactionBase(BaseModel):
    posted_at: datetime | None = None
    payee: str | None = None
    note: str | None = None
    external_id: str | None = None
    category_id: UUID | None = None

    model_config = STRICT

    @field_validator("category_id", mode="before")
    def _validate_category(cls, v):
        if v is None:
            return None
        return UUID(str(v))


class TransactionCreate(TransactionBase):
    postings: list[PostingCreate] = Field(default_factory=list)

    model_config = STRICT

    @field_validator("posted_at", mode="before")
    def _parse_posted_at(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        return datetime.fromisoformat(str(v))


class TransactionUpdate(BaseModel):
    posted_at: datetime | None = None
    payee: str | None = None
    note: str | None = None
    external_id: str | None = None
    category_id: UUID | None = None

    model_config = STRICT


class Transaction(TransactionBase):
    id: UUID
    user_id: UUID
    posted_at: datetime

    model_config = ORM_STRICT
