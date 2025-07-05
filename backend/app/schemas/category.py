from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator, condecimal

STRICT = ConfigDict(strict=True, json_encoders={Decimal: lambda v: float(v)})
ORM_STRICT = ConfigDict(
    from_attributes=True, strict=True, json_encoders={Decimal: lambda v: float(v)}
)


Amount = condecimal(max_digits=20, decimal_places=6, strict=False)


class CategoryBase(BaseModel):
    name: str
    monthly_limit: Amount | None = None
    icon: str | None = None
    parent_id: UUID | None = None

    model_config = STRICT

    @field_validator("parent_id", mode="before")
    def _validate_parent(cls, v):
        if v is None:
            return None
        return UUID(str(v))


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    monthly_limit: Amount | None = None
    icon: str | None = None
    parent_id: UUID | None = None

    model_config = STRICT

    @field_validator("parent_id", mode="before")
    def _validate_parent(cls, v):
        if v is None:
            return None
        return UUID(str(v))


class Category(CategoryBase):
    id: UUID
    account_id: UUID
    user_id: UUID

    model_config = ORM_STRICT
