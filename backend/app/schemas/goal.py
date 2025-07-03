from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(from_attributes=True, strict=True)


class GoalBase(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0
    due_date: datetime | None = None

    model_config = STRICT


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: str | None = None
    target_amount: float | None = None
    current_amount: float | None = None
    due_date: datetime | None = None

    model_config = STRICT


class GoalDeposit(BaseModel):
    amount: float

    model_config = STRICT


class Goal(GoalBase):
    id: UUID
    account_id: UUID
    user_id: UUID

    model_config = ORM_STRICT
