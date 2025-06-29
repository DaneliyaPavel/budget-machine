"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI
from .routers import transactions, categories, goals, users
from .database import engine, Base
import asyncio

tags_metadata = [
    {"name": "Категории", "description": "Управление категориями операций"},
    {"name": "Операции", "description": "Доходы и расходы"},
    {"name": "Цели", "description": "Накопления и цели"},
    {"name": "Пользователи", "description": "Регистрация и авторизация"},
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
