from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator, condecimal

STRICT = ConfigDict(strict=True, json_encoders={Decimal: lambda v: float(v)})
ORM_STRICT = ConfigDict(
    from_attributes=True, strict=True, json_encoders={Decimal: lambda v: float(v)}
)


Amount = condecimal(max_digits=20, decimal_places=6, strict=False)


class PostingBase(BaseModel):
    amount: Amount
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
