from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class PostingBase(BaseModel):
    amount: float
    side: str
    account_id: UUID
    currency_code: str | None = None

    model_config = STRICT

    @field_validator("account_id", mode="before")
    def _validate_account_id(cls, v):
        return UUID(str(v))


class PostingCreate(PostingBase):
    pass


class Posting(PostingBase):
    id: UUID
    transaction_id: UUID

    model_config = ORM_STRICT
