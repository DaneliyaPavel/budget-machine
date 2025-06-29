"""Функции для взаимодействия с базой данных."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from . import models, schemas

async def get_categories(db: AsyncSession):
    """Получить все категории."""
    result = await db.execute(select(models.Category))
    return result.scalars().all()

async def get_category(db: AsyncSession, category_id: int):
    """Найти категорию по идентификатору."""
    result = await db.execute(select(models.Category).where(models.Category.id == category_id))
    return result.scalar_one_or_none()

async def create_category(db: AsyncSession, category: schemas.CategoryCreate):
    """Создать новую категорию."""
    db_obj = models.Category(name=category.name)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_category(db: AsyncSession, category_id: int, data: schemas.CategoryUpdate):
    """Обновить данные категории."""
    stmt = update(models.Category).where(models.Category.id == category_id).values(**data.dict(exclude_unset=True)).returning(models.Category)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_category(db: AsyncSession, category_id: int):
    """Удалить категорию."""
    await db.execute(delete(models.Category).where(models.Category.id == category_id))
    await db.commit()

async def get_transactions(db: AsyncSession):
    """Получить список всех операций."""
    result = await db.execute(select(models.Transaction))
    return result.scalars().all()

async def get_transaction(db: AsyncSession, tx_id: int):
    """Получить операцию по идентификатору."""
    result = await db.execute(select(models.Transaction).where(models.Transaction.id == tx_id))
    return result.scalar_one_or_none()

async def create_transaction(db: AsyncSession, tx: schemas.TransactionCreate):
    """Создать финансовую операцию."""
    db_obj = models.Transaction(**tx.dict())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_transaction(db: AsyncSession, tx_id: int, data: schemas.TransactionUpdate):
    """Обновить данные операции."""
    stmt = update(models.Transaction).where(models.Transaction.id == tx_id).values(**data.dict(exclude_unset=True)).returning(models.Transaction)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_transaction(db: AsyncSession, tx_id: int):
    """Удалить операцию."""
    await db.execute(delete(models.Transaction).where(models.Transaction.id == tx_id))
    await db.commit()

async def get_goals(db: AsyncSession):
    """Получить все цели накоплений."""
    result = await db.execute(select(models.Goal))
    return result.scalars().all()

async def get_goal(db: AsyncSession, goal_id: int):
    """Найти цель по идентификатору."""
    result = await db.execute(select(models.Goal).where(models.Goal.id == goal_id))
    return result.scalar_one_or_none()

async def create_goal(db: AsyncSession, goal: schemas.GoalCreate):
    """Создать новую цель накоплений."""
    db_obj = models.Goal(**goal.dict())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_goal(db: AsyncSession, goal_id: int, data: schemas.GoalUpdate):
    """Обновить цель накоплений."""
    stmt = update(models.Goal).where(models.Goal.id == goal_id).values(**data.dict(exclude_unset=True)).returning(models.Goal)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_goal(db: AsyncSession, goal_id: int):
    """Удалить цель."""
    await db.execute(delete(models.Goal).where(models.Goal.id == goal_id))
    await db.commit()

from .security import get_password_hash

async def get_user_by_email(db: AsyncSession, email: str):
    """Найти пользователя по email."""
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    """Создать пользователя с хешированным паролем."""
    hashed = get_password_hash(user.password)
    db_obj = models.User(email=user.email, hashed_password=hashed)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
