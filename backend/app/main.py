"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
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
    tokens,
    jobs,
    oauth,
    currency,
    push,
)
from .database import engine, Base
from .kafka_producer import close as close_producer
from contextlib import asynccontextmanager

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
    {"name": "Токены", "description": "OAuth-токены банков"},
    {"name": "Задания", "description": "Фоновые задачи"},
    {"name": "OAuth", "description": "Авторизация через Тинькофф ID"},
    {"name": "Валюты", "description": "Курсы и конвертация"},
    {"name": "Уведомления", "description": "Web Push подписки"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events using lifespan."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        Instrumentator().instrument(app).expose(app)
    except RuntimeError:
        pass
    yield
    await close_producer()


app = FastAPI(
    title="Учет бюджета",
    description="Простой API для ведения личных финансов",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)


app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(users.router)
app.include_router(analytics.router)
app.include_router(tinkoff.router)
app.include_router(banks.router)
app.include_router(recurring.router)
app.include_router(accounts.router)
app.include_router(tokens.router)
app.include_router(jobs.router)
app.include_router(oauth.router)
app.include_router(currency.router)
app.include_router(push.router)
