from uuid import UUID
from pydantic import BaseModel, ConfigDict

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class BankTokenBase(BaseModel):
    bank: str

    model_config = STRICT


class BankTokenCreate(BankTokenBase):
    token: str

    model_config = STRICT


class BankToken(BankTokenBase):
    id: UUID
    token: str
    account_id: UUID
    user_id: UUID

    model_config = ORM_STRICT
