"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from .routers import (
    goals,
    analytics,
    tinkoff,
    banks,
    recurring,
    tokens,
    jobs,
    oauth,
    push,
)
from .api.v1 import (
    auth as auth_v1,
    accounts as accounts_v1,
    categories as categories_v1,
    transactions as transactions_v1,
    users as users_v1,
    currencies as currencies_v1,
)
from .database import engine
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
    {"name": "Auth", "description": "Signup and JWT auth"},
    {"name": "Валюты", "description": "Курсы и конвертация"},
    {"name": "Уведомления", "description": "Web Push подписки"},
    {"name": "Сервис", "description": "Системные маршруты"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events using lifespan."""
    async with engine.begin() as _conn:
        # База данных инициализируется миграциями Alembic. Таблицы не
        # создаются автоматически при запуске приложения.
        # await conn.run_sync(Base.metadata.create_all)
        pass
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


@app.exception_handler(FastAPIHTTPException)
async def custom_http_exception_handler(
    request: Request, exc: FastAPIHTTPException
) -> JSONResponse:
    """Return errors in a consistent JSON format."""
    if isinstance(exc.detail, dict) and {"detail", "code"} <= exc.detail.keys():
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail["detail"], "code": exc.detail["code"]},
            headers=exc.headers,
        )
    return await http_exception_handler(request, exc)


app.include_router(categories_v1.router)
app.include_router(transactions_v1.router)
app.include_router(goals.router)
app.include_router(users_v1.router)
app.include_router(analytics.router)
app.include_router(tinkoff.router)
app.include_router(banks.router)
app.include_router(recurring.router)
app.include_router(accounts_v1.router)
app.include_router(tokens.router)
app.include_router(jobs.router)
app.include_router(oauth.router)
app.include_router(auth_v1.router)
app.include_router(currencies_v1.router)
app.include_router(push.router)


@app.get("/health", tags=["Сервис"])
async def health() -> dict[str, str]:
    """Проверка работоспособности приложения."""
    return {"status": "ok"}
