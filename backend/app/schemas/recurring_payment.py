from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class RecurringPaymentBase(BaseModel):
    name: str
    amount: float
    currency: str = "RUB"
    day: int
    description: str | None = None
    category_id: UUID

    model_config = STRICT

    @field_validator("category_id", mode="before")
    def _validate_category(cls, v):
        return UUID(str(v))


class RecurringPaymentCreate(RecurringPaymentBase):
    pass


class RecurringPaymentUpdate(BaseModel):
    name: str | None = None
    amount: float | None = None
    currency: str | None = None
    day: int | None = None
    description: str | None = None
    category_id: UUID | None = None
    active: bool | None = None

    model_config = STRICT

    @field_validator("category_id", mode="before")
    def _validate_category(cls, v):
        if v is None:
            return None
        return UUID(str(v))


class RecurringPayment(RecurringPaymentBase):
    id: UUID
    account_id: UUID
    user_id: UUID
    active: bool

    model_config = ORM_STRICT
