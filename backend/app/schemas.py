"""Pydantic-схемы для API."""

from datetime import datetime, date as date_
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID


class Account(BaseModel):
    """Информация об общем счёте."""

    id: UUID
    name: str
    currency_code: str = "RUB"
    type: str = "cash"
    user_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    """Базовые поля категории."""

    name: str
    monthly_limit: float | None = None
    parent_id: UUID | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    """Поля для обновления категории."""

    name: str | None = None
    monthly_limit: float | None = None
    parent_id: UUID | None = None


class Category(CategoryBase):
    id: UUID
    account_id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    """Общие поля финансовой операции."""

    amount: float
    currency: str = "RUB"
    amount_rub: float | None = None
    description: Optional[str] = None
    category_id: UUID


class TransactionCreate(TransactionBase):
    created_at: datetime | None = None
    pass


class TransactionUpdate(BaseModel):
    """Параметры для обновления операции."""

    amount: float | None = None
    currency: str | None = None
    description: str | None = None
    category_id: UUID | None = None
    created_at: datetime | None = None


class Transaction(TransactionBase):
    id: UUID
    created_at: datetime
    amount_rub: float
    account_id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class GoalBase(BaseModel):
    """Основные поля цели накоплений."""

    name: str
    target_amount: float
    current_amount: float = 0
    due_date: Optional[datetime] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    """Параметры для изменения цели."""

    name: str | None = None
    target_amount: float | None = None
    current_amount: float | None = None
    due_date: datetime | None = None


class GoalDeposit(BaseModel):
    """Сумма пополнения цели."""

    amount: float


class Goal(GoalBase):
    id: UUID
    account_id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class RecurringPaymentBase(BaseModel):
    """Общие поля регулярного платежа."""

    name: str
    amount: float
    currency: str = "RUB"
    day: int
    description: str | None = None
    category_id: UUID


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


class RecurringPayment(RecurringPaymentBase):
    id: UUID
    account_id: UUID
    user_id: UUID
    active: bool

    model_config = ConfigDict(from_attributes=True)


class BankTokenBase(BaseModel):
    """Основа токена банка."""

    bank: str


class BankTokenCreate(BankTokenBase):
    token: str


class BankToken(BankTokenBase):
    id: UUID
    token: str
    account_id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    """Данные пользователя."""

    email: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None


class JoinAccount(BaseModel):
    """Параметры для присоединения к существующему счёту."""

    account_id: UUID


class User(UserBase):
    id: UUID
    is_active: bool
    account_id: UUID
    role: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class CategorySummary(BaseModel):
    """Сводные данные по категории расходов."""

    category: str = Field(..., description="Название категории")
    total: float = Field(..., description="Сумма операций")


class LimitExceed(BaseModel):
    """Категория, в которой превышен месячный лимит."""

    category: str = Field(..., description="Название категории")
    limit: float = Field(..., description="Установленный лимит")
    spent: float = Field(..., description="Фактические траты")


class ForecastItem(BaseModel):
    """Прогноз трат по категории на месяц."""

    category: str = Field(..., description="Название категории")
    spent: float = Field(..., description="Уже потрачено")
    forecast: float = Field(..., description="Ожидаемые траты к концу месяца")


class DailySummary(BaseModel):
    """Сумма расходов за конкретный день."""

    date: date_ = Field(..., description="Дата")
    total: float = Field(..., description="Потрачено за день")


class MonthlySummary(BaseModel):
    """Итог и прогноз расходов за месяц."""

    spent: float = Field(..., description="Потрачено на текущий момент")
    forecast: float = Field(..., description="Ожидаемые траты к концу месяца")


class GoalProgress(BaseModel):
    """Текущий прогресс по цели накоплений."""

    id: UUID = Field(..., description="Идентификатор цели")
    name: str = Field(..., description="Название цели")
    target_amount: float = Field(..., description="Сумма, которую нужно накопить")
    current_amount: float = Field(..., description="Уже накоплено")
    progress: float = Field(..., description="Выполнение цели в процентах")
    due_date: datetime | None = Field(None, description="Желаемая дата достижения")


class PushSubscriptionBase(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class PushSubscriptionCreate(PushSubscriptionBase):
    pass


class PushSubscription(PushSubscriptionBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
