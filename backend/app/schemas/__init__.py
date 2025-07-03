"""Pydantic-схемы для API."""

from datetime import datetime, date as date_
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from ..models import AccountType

STRICT = ConfigDict(strict=True)
ORM_STRICT = ConfigDict(
    from_attributes=True,
    strict=True,
    json_encoders={AccountType: lambda v: v.value},
)


class Account(BaseModel):
    """Информация об общем счёте."""

    id: UUID
    name: str
    currency_code: str = "RUB"
    type: str = "cash"
    user_id: UUID | None = None

    model_config = ORM_STRICT

    @field_validator("type", mode="before")
    def _validate_type(cls, v):
        return v.value if isinstance(v, AccountType) else v

    @field_validator("id", mode="before")
    def _validate_id(cls, v):
        return UUID(str(v))


class CategoryBase(BaseModel):
    """Базовые поля категории."""

    name: str
    monthly_limit: float | None = None
    parent_id: UUID | None = None

    model_config = STRICT

    @field_validator("parent_id", mode="before")
    def _validate_parent(cls, v):
        if v is None:
            return None
        return UUID(str(v))


class CategoryCreate(CategoryBase):
    model_config = STRICT


class CategoryUpdate(BaseModel):
    """Поля для обновления категории."""

    name: str | None = None
    monthly_limit: float | None = None
    parent_id: UUID | None = None

    model_config = STRICT


class Category(CategoryBase):
    id: UUID
    account_id: UUID
    user_id: UUID

    model_config = ORM_STRICT


class TransactionBase(BaseModel):
    """Общие поля финансовой операции."""

    amount: float
    currency: str = "RUB"
    amount_rub: float | None = None
    description: Optional[str] = None
    category_id: UUID

    model_config = STRICT

    @field_validator("category_id", mode="before")
    def _validate_category(cls, v: UUID | str):
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
    """Параметры для обновления операции."""

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


class PostingBase(BaseModel):
    amount: float
    side: str
    account_id: UUID

    model_config = STRICT


class PostingCreate(PostingBase):
    model_config = STRICT


class Posting(PostingBase):
    id: UUID
    transaction_id: UUID

    model_config = ORM_STRICT


class GoalBase(BaseModel):
    """Основные поля цели накоплений."""

    name: str
    target_amount: float
    current_amount: float = 0
    due_date: Optional[datetime] = None

    model_config = STRICT


class GoalCreate(GoalBase):
    model_config = STRICT


class GoalUpdate(BaseModel):
    """Параметры для изменения цели."""

    name: str | None = None
    target_amount: float | None = None
    current_amount: float | None = None
    due_date: datetime | None = None

    model_config = STRICT


class GoalDeposit(BaseModel):
    """Сумма пополнения цели."""

    amount: float

    model_config = STRICT


class Goal(GoalBase):
    id: UUID
    account_id: UUID
    user_id: UUID

    model_config = ORM_STRICT


class RecurringPaymentBase(BaseModel):
    """Общие поля регулярного платежа."""

    name: str
    amount: float
    currency: str = "RUB"
    day: int
    description: str | None = None
    category_id: UUID

    model_config = STRICT

    @field_validator("category_id", mode="before")
    def _validate_rp_category(cls, v: UUID | str):
        return UUID(str(v))


class RecurringPaymentCreate(RecurringPaymentBase):
    model_config = STRICT


class RecurringPaymentUpdate(BaseModel):
    name: str | None = None
    amount: float | None = None
    currency: str | None = None
    day: int | None = None
    description: str | None = None
    category_id: UUID | None = None
    active: bool | None = None

    model_config = STRICT


class RecurringPayment(RecurringPaymentBase):
    id: UUID
    account_id: UUID
    user_id: UUID
    active: bool

    model_config = ORM_STRICT


class BankTokenBase(BaseModel):
    """Основа токена банка."""

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


class UserBase(BaseModel):
    """Данные пользователя."""

    email: str

    model_config = STRICT


class UserCreate(UserBase):
    password: str

    model_config = STRICT


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None

    model_config = STRICT


class JoinAccount(BaseModel):
    """Параметры для присоединения к существующему счёту."""

    account_id: UUID

    model_config = STRICT

    @field_validator("account_id", mode="before")
    def _validate_account(cls, v: UUID | str):
        return UUID(str(v))


class User(UserBase):
    id: UUID
    is_active: bool
    account_id: UUID
    role: str

    model_config = ORM_STRICT


class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = STRICT


class TokenPair(Token):
    refresh_token: str

    model_config = STRICT


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
    type: str | None = None

    model_config = STRICT


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = STRICT


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = STRICT


class CategorySummary(BaseModel):
    """Сводные данные по категории расходов."""

    category: str = Field(..., description="Название категории")
    total: float = Field(..., description="Сумма операций")

    model_config = STRICT


class LimitExceed(BaseModel):
    """Категория, в которой превышен месячный лимит."""

    category: str = Field(..., description="Название категории")
    limit: float = Field(..., description="Установленный лимит")
    spent: float = Field(..., description="Фактические траты")

    model_config = STRICT


class ForecastItem(BaseModel):
    """Прогноз трат по категории на месяц."""

    category: str = Field(..., description="Название категории")
    spent: float = Field(..., description="Уже потрачено")
    forecast: float = Field(..., description="Ожидаемые траты к концу месяца")

    model_config = STRICT


class DailySummary(BaseModel):
    """Сумма расходов за конкретный день."""

    date: date_ = Field(..., description="Дата")
    total: float = Field(..., description="Потрачено за день")

    model_config = STRICT


class MonthlySummary(BaseModel):
    """Итог и прогноз расходов за месяц."""

    spent: float = Field(..., description="Потрачено на текущий момент")
    forecast: float = Field(..., description="Ожидаемые траты к концу месяца")

    model_config = STRICT


class GoalProgress(BaseModel):
    """Текущий прогресс по цели накоплений."""

    id: UUID = Field(..., description="Идентификатор цели")
    name: str = Field(..., description="Название цели")
    target_amount: float = Field(..., description="Сумма, которую нужно накопить")
    current_amount: float = Field(..., description="Уже накоплено")
    progress: float = Field(..., description="Выполнение цели в процентах")
    due_date: datetime | None = Field(None, description="Желаемая дата достижения")

    model_config = STRICT


class PushSubscriptionBase(BaseModel):
    endpoint: str
    p256dh: str
    auth: str

    model_config = STRICT


class PushSubscriptionCreate(PushSubscriptionBase):
    model_config = STRICT


class PushSubscription(PushSubscriptionBase):
    id: UUID

    model_config = ORM_STRICT
