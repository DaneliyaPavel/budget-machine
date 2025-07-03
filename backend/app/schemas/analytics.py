from datetime import datetime, date as date_
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

STRICT = ConfigDict(strict=True)


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
