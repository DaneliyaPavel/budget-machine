"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI
from .routers import (
    transactions,
    categories,
    goals,
    users,
    analytics,
    tinkoff,
    banks,
    recurring,
    accounts,
)
from .database import engine, Base

tags_metadata = [
    {"name": "Категории", "description": "Управление категориями операций"},
    {"name": "Операции", "description": "Доходы и расходы"},
    {"name": "Цели", "description": "Накопления и цели"},
    {"name": "Пользователи", "description": "Регистрация и авторизация"},
    {"name": "Аналитика", "description": "Сводные отчёты"},
    {"name": "Тинькофф", "description": "Импорт операций из банка"},
    {"name": "Банки", "description": "Импорт операций из разных банков"},
    {"name": "Регулярные платежи", "description": "Повторяющиеся операции"},
    {"name": "Счёт", "description": "Управление общим счётом"},
]

app = FastAPI(
    title="Учет бюджета",
    description="Простой API для ведения личных финансов",
    openapi_tags=tags_metadata,
)


@app.on_event("startup")
async def on_startup():
    """Создаём таблицы при запуске приложения."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(users.router)
app.include_router(analytics.router)
app.include_router(tinkoff.router)
app.include_router(banks.router)
app.include_router(recurring.router)
app.include_router(accounts.router)
