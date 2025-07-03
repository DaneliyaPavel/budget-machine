from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

STRICT = ConfigDict(strict=True)


class Posting(BaseModel):
    amount: float
    side: str
    account_id: UUID

    model_config = STRICT


class PostEntryRequest(BaseModel):
    amount: float
    currency: str
    description: str | None = None
    category_id: UUID
    created_at: datetime | None = None
    postings: list[Posting]
    account_id: UUID
    user_id: UUID

    model_config = STRICT


class Txn(BaseModel):
    id: UUID
    amount: float
    currency: str
    amount_rub: float
    description: str | None = None
    category_id: UUID
    created_at: datetime
    account_id: UUID
    user_id: UUID

    model_config = STRICT


class TxnId(BaseModel):
    id: UUID

    model_config = STRICT


class BalanceRequest(BaseModel):
    account_id: UUID
    at: datetime | None = None

    model_config = STRICT


class BalanceResponse(BaseModel):
    amount: float

    model_config = STRICT


class StreamRequest(BaseModel):
    account_id: UUID
    start: datetime | None = None
    end: datetime | None = None

    model_config = STRICT
