"""Pydantic-схемы для API."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class CategoryBase(BaseModel):
    """Базовые поля категории."""
    name: str
    monthly_limit: float | None = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    """Поля для обновления категории."""
    name: str | None = None
    monthly_limit: float | None = None

class Category(CategoryBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    """Общие поля финансовой операции."""
    amount: float
    currency: str = "RUB"
    amount_rub: float | None = None
    description: Optional[str] = None
    category_id: int

class TransactionCreate(TransactionBase):
    created_at: datetime | None = None

class TransactionUpdate(BaseModel):
    """Параметры для обновления операции."""
    amount: float | None = None
    currency: str | None = None
    description: str | None = None
    category_id: int | None = None
    created_at: datetime | None = None

class Transaction(TransactionBase):
    id: int
    created_at: datetime
    amount_rub: float
    user_id: int

    class Config:
        orm_mode = True

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

class Goal(GoalBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    """Данные пользователя."""
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

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
