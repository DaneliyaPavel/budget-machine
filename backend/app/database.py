"""Настройка подключения к базе данных."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# строка подключения берется из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# если переменная окружения DB_ECHO установлена в true/1/yes, включаем логгирование SQL
DB_ECHO = os.getenv("DB_ECHO", "0").lower() in {"1", "true", "yes"}

# создаём движок и фабрику сессий
RUNNING_ALEMBIC = os.getenv("RUNNING_ALEMBIC") == "1"

if not RUNNING_ALEMBIC:
    engine = create_async_engine(DATABASE_URL, echo=DB_ECHO)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
else:
    engine = None
    async_session = None


class Base(DeclarativeBase):
    """Базовый класс для всех моделей ORM."""

    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессий БД."""
    async with async_session() as session:
        yield session
