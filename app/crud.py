"""Функции для взаимодействия с базой данных."""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from . import models, schemas, currency
from .security import get_password_hash

async def get_categories(db: AsyncSession, account_id: int):
    """Получить все категории счёта."""
    result = await db.execute(
        select(models.Category).where(models.Category.account_id == account_id)
    )
    return result.scalars().all()

async def get_category(db: AsyncSession, category_id: int, account_id: int):
    """Найти категорию счёта по идентификатору."""
    result = await db.execute(
        select(models.Category).where(
            models.Category.id == category_id, models.Category.account_id == account_id
        )
    )
    return result.scalar_one_or_none()

async def create_category(
    db: AsyncSession,
    category: schemas.CategoryCreate,
    account_id: int,
    user_id: int,
):
    """Создать новую категорию в счёте."""
    db_obj = models.Category(
        name=category.name,
        monthly_limit=category.monthly_limit,
        account_id=account_id,
        user_id=user_id,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_category(
    db: AsyncSession,
    category_id: int,
    data: schemas.CategoryUpdate,
    account_id: int,
) -> models.Category | None:
    """Обновить данные категории пользователя."""
    stmt = (
        update(models.Category)
        .where(models.Category.id == category_id, models.Category.account_id == account_id)
        .values(**data.dict(exclude_unset=True))
        .returning(models.Category)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_category(db: AsyncSession, category_id: int, account_id: int):
    """Удалить категорию счёта."""
    await db.execute(
        delete(models.Category).where(
            models.Category.id == category_id, models.Category.account_id == account_id
        )
    )
    await db.commit()

async def get_transactions(db: AsyncSession, account_id: int):
    """Получить список всех операций счёта."""
    result = await db.execute(
        select(models.Transaction).where(models.Transaction.account_id == account_id)
    )
    return result.scalars().all()

async def get_transaction(db: AsyncSession, tx_id: int, account_id: int):
    """Получить операцию счёта по идентификатору."""
    result = await db.execute(
        select(models.Transaction).where(
            models.Transaction.id == tx_id,
            models.Transaction.account_id == account_id,
        )
    )
    return result.scalar_one_or_none()

async def create_transaction(
    db: AsyncSession,
    tx: schemas.TransactionCreate,
    account_id: int,
    user_id: int,
):
    """Создать финансовую операцию."""
    rate = await currency.get_rate(tx.currency)
    db_obj = models.Transaction(
        **tx.dict(exclude_unset=True),
        amount_rub=tx.amount * rate,
        account_id=account_id,
        user_id=user_id,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def create_transactions_bulk(
    db: AsyncSession,
    txs: list[schemas.TransactionCreate],
    account_id: int,
    user_id: int,
):
    """Создать сразу несколько операций пользователя."""
    objects = []
    for tx in txs:
        rate = await currency.get_rate(tx.currency)
        objects.append(
            models.Transaction(
                **tx.dict(exclude_unset=True),
                amount_rub=tx.amount * rate,
                account_id=account_id,
                user_id=user_id,
            )
        )
    db.add_all(objects)
    await db.commit()
    for obj in objects:
        await db.refresh(obj)
    return objects

async def update_transaction(
    db: AsyncSession,
    tx_id: int,
    data: schemas.TransactionUpdate,
    account_id: int,
    user_id: int,
) -> models.Transaction | None:
    """Обновить данные операции пользователя."""
    tx_obj = await get_transaction(db, tx_id, account_id)
    if not tx_obj:
        return None
    update_data = data.dict(exclude_unset=True)
    if "currency" in update_data or "amount" in update_data:
        currency_code = update_data.get("currency", tx_obj.currency)
        amount_val = update_data.get("amount", tx_obj.amount)
        rate = await currency.get_rate(currency_code)
        update_data["amount_rub"] = amount_val * rate
    for key, value in update_data.items():
        setattr(tx_obj, key, value)
    await db.commit()
    await db.refresh(tx_obj)
    return tx_obj

async def delete_transaction(db: AsyncSession, tx_id: int, account_id: int):
    """Удалить операцию."""
    await db.execute(
        delete(models.Transaction).where(
            models.Transaction.id == tx_id,
            models.Transaction.account_id == account_id,
        )
    )
    await db.commit()

async def get_goals(db: AsyncSession, account_id: int):
    """Получить все цели счёта."""
    result = await db.execute(
        select(models.Goal).where(models.Goal.account_id == account_id)
    )
    return result.scalars().all()

async def get_goal(db: AsyncSession, goal_id: int, account_id: int):
    """Найти цель счёта по идентификатору."""
    result = await db.execute(
        select(models.Goal).where(
            models.Goal.id == goal_id,
            models.Goal.account_id == account_id,
        )
    )
    return result.scalar_one_or_none()

async def create_goal(
    db: AsyncSession,
    goal: schemas.GoalCreate,
    account_id: int,
    user_id: int,
) -> models.Goal:
    """Создать новую цель пользователя."""
    db_obj = models.Goal(
        **goal.dict(), account_id=account_id, user_id=user_id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_goal(
    db: AsyncSession,
    goal_id: int,
    data: schemas.GoalUpdate,
    account_id: int,
) -> models.Goal | None:
    """Обновить цель пользователя."""
    stmt = (
        update(models.Goal)
        .where(models.Goal.id == goal_id, models.Goal.account_id == account_id)
        .values(**data.dict(exclude_unset=True))
        .returning(models.Goal)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_goal(db: AsyncSession, goal_id: int, account_id: int):
    """Удалить цель пользователя."""
    await db.execute(
        delete(models.Goal).where(
            models.Goal.id == goal_id, models.Goal.account_id == account_id
        )
    )
    await db.commit()

async def get_user_by_email(db: AsyncSession, email: str):
    """Найти пользователя по email."""
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    """Создать пользователя с хешированным паролем."""
    hashed = get_password_hash(user.password)
    account = models.Account(name="Личный бюджет")
    db.add(account)
    await db.flush()
    db_obj = models.User(email=user.email, hashed_password=hashed, account=account)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def join_account(db: AsyncSession, user: models.User, account_id: int) -> models.User | None:
    """Присоединить пользователя к существующему счёту."""
    account = await db.get(models.Account, account_id)
    if not account:
        return None
    user.account_id = account_id
    await db.commit()
    await db.refresh(user)
    return user


async def transactions_summary_by_category(
    db: AsyncSession, start: datetime, end: datetime, account_id: int
):
    """Вернуть сумму операций пользователя по категориям за период."""
    stmt = (
        select(models.Category.name, func.sum(models.Transaction.amount_rub))
        .join(models.Transaction)
        .where(
            models.Transaction.created_at >= start,
            models.Transaction.created_at < end,
            models.Transaction.account_id == account_id,
        )
        .group_by(models.Category.name)
    )
    result = await db.execute(stmt)
    return result.all()


async def categories_over_limit(
    db: AsyncSession, start: datetime, end: datetime, account_id: int
):
    """Список категорий пользователя, где траты превысили лимит."""
    stmt = (
        select(
            models.Category.name,
            models.Category.monthly_limit,
            func.sum(models.Transaction.amount_rub).label("spent"),
        )
        .join(models.Transaction)
        .where(
            models.Transaction.created_at >= start,
            models.Transaction.created_at < end,
            models.Category.monthly_limit.isnot(None),
            models.Transaction.account_id == account_id,
        )
        .group_by(models.Category.id)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [r for r in rows if r[2] > r[1]]


async def forecast_by_category(
    db: AsyncSession, start: datetime, end: datetime, account_id: int
):
    """Прогноз трат пользователя до конца периода."""
    now = datetime.utcnow()
    if now < start:
        return []
    elapsed_days = (now - start).days + 1
    total_days = (end - start).days
    stmt = (
        select(
            models.Category.name,
            func.sum(models.Transaction.amount_rub).label("spent"),
        )
        .join(models.Transaction)
        .where(
            models.Transaction.created_at >= start,
            models.Transaction.created_at < now,
            models.Transaction.account_id == account_id,
        )
        .group_by(models.Category.name)
    )
    result = await db.execute(stmt)
    rows = result.all()
    forecast = []
    for name, spent in rows:
        proj = float(spent or 0) / elapsed_days * total_days
        forecast.append((name, float(spent or 0), proj))
    return forecast


async def daily_expenses(
    db: AsyncSession, start: datetime, end: datetime, account_id: int
):
    """Суммы трат по дням за указанный период."""

    day = func.date_trunc("day", models.Transaction.created_at)
    stmt = (
        select(day.label("day"), func.sum(models.Transaction.amount_rub))
        .where(
            models.Transaction.created_at >= start,
            models.Transaction.created_at < end,
            models.Transaction.account_id == account_id,
        )
        .group_by(day)
        .order_by(day)
    )
    result = await db.execute(stmt)
    return result.all()


async def monthly_overview(
    db: AsyncSession, start: datetime, end: datetime, account_id: int
):
    """Текущие траты и прогноз до конца месяца."""

    now = datetime.utcnow()
    cutoff = min(now, end)
    stmt = (
        select(func.sum(models.Transaction.amount_rub))
        .where(
            models.Transaction.created_at >= start,
            models.Transaction.created_at < cutoff,
            models.Transaction.account_id == account_id,
        )
    )
    result = await db.execute(stmt)
    spent = float(result.scalar() or 0)

    elapsed_days = (cutoff - start).days + 1
    total_days = (end - start).days
    forecast = spent / elapsed_days * total_days if elapsed_days else 0
    return spent, forecast
