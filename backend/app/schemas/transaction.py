from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .posting import PostingCreate

STRICT = ConfigDict(strict=True, populate_by_name=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True, populate_by_name=True)


class TransactionBase(BaseModel):
    posted_at: datetime | None = Field(
        None, alias="created_at"
    )
    payee: str | None = None
    note: str | None = Field(None, alias="description")
    external_id: str | None = None
    category_id: UUID | None = None

    model_config = STRICT

    @field_validator("category_id", mode="before")
    def _validate_category(cls, v):
        if v is None:
            return None
        return UUID(str(v))


class TransactionCreate(TransactionBase):
    amount: float | None = None
    currency: str | None = None
    postings: list[PostingCreate] = Field(default_factory=list)

    model_config = STRICT

    @field_validator("posted_at", mode="before")
    def _parse_posted_at(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        return datetime.fromisoformat(str(v))


class TransactionUpdate(BaseModel):
    posted_at: datetime | None = Field(None, alias="created_at")
    payee: str | None = None
    note: str | None = Field(None, alias="description")
    external_id: str | None = None
    category_id: UUID | None = None

    model_config = STRICT


class Transaction(TransactionBase):
    id: UUID
    user_id: UUID
    posted_at: datetime = Field(alias="created_at")

    model_config = ORM_STRICT
