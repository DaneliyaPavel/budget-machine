"""Настройка подключения к базе данных."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# строка подключения берется из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# создаём движок и фабрику сессий
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей ORM."""

    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессий БД."""
    async with async_session() as session:
        yield session
