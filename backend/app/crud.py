"""Функции для взаимодействия с базой данных."""

from datetime import datetime, timezone
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
import uuid

from . import models, schemas, currency, vault
from .security import get_password_hash


# ----------------------------------------------------------------------------
# Пользователи
# ----------------------------------------------------------------------------


async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    """Найти пользователя по email."""
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    """Создать пользователя и счёт."""
    hashed = get_password_hash(user.password)
    account = models.Account(name="Личный бюджет", currency_code="RUB")
    db.add(account)
    await db.flush()
    db_obj = models.User(
        email=user.email,
        hashed_password=hashed,
        account=account,
        role="owner",
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def create_user_oauth(db: AsyncSession, email: str) -> models.User:
    """Создать пользователя через OAuth."""
    hashed = get_password_hash(secrets.token_hex(8))
    account = models.Account(name="Личный бюджет", currency_code="RUB")
    db.add(account)
    await db.flush()
    user = models.User(
        email=email, hashed_password=hashed, account=account, role="owner"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def join_account(
    db: AsyncSession, user: models.User, account_id: uuid.UUID
) -> models.User | None:
    """Присоединить пользователя к существующему счёту."""
    account = await db.get(models.Account, account_id)
    if not account:
        return None
    user.account_id = account_id
    user.role = "member"
    await db.commit()
    await db.refresh(user)
    return user


async def get_account_users(db: AsyncSession, account_id: uuid.UUID):
    """Получить всех пользователей счёта."""
    result = await db.execute(
        select(models.User).where(models.User.account_id == account_id)
    )
    return result.scalars().all()


async def delete_user(
    db: AsyncSession, user_id: uuid.UUID, account_id: uuid.UUID
) -> bool:
    """Удалить пользователя из счёта."""
    result = await db.execute(
        delete(models.User).where(
            models.User.id == user_id,
            models.User.account_id == account_id,
        )
    )
    await db.commit()
    return result.rowcount > 0


async def update_user(
    db: AsyncSession,
    user: models.User,
    data: schemas.UserUpdate,
) -> models.User:
    """Обновить данные пользователя."""
    if data.email is not None:
        user.email = data.email
    if data.password is not None:
        user.hashed_password = get_password_hash(data.password)
    await db.commit()
    await db.refresh(user)
    return user


# ----------------------------------------------------------------------------
# Аккаунты
# ----------------------------------------------------------------------------


async def get_account(db: AsyncSession, account_id: uuid.UUID) -> models.Account | None:
    """Получить счёт по идентификатору."""
    return await db.get(models.Account, account_id)


async def update_account(
    db: AsyncSession,
    account_id: uuid.UUID,
    name: str | None = None,
    currency_code: str | None = None,
) -> models.Account | None:
    """Изменить параметры счёта."""
    values = {}
    if name is not None:
        values["name"] = name
    if currency_code is not None:
        values["currency_code"] = currency_code
    if not values:
        return await get_account(db, account_id)
    stmt = (
        update(models.Account)
        .where(models.Account.id == account_id)
        .values(**values)
        .returning(models.Account)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()


# ----------------------------------------------------------------------------
# Категории
# ----------------------------------------------------------------------------


async def get_categories(db: AsyncSession, account_id: uuid.UUID):
    result = await db.execute(
        select(models.Category).where(models.Category.account_id == account_id)
    )
    return result.scalars().all()


async def get_category(db: AsyncSession, category_id: uuid.UUID, account_id: uuid.UUID):
    result = await db.execute(
        select(models.Category).where(
            models.Category.id == category_id,
            models.Category.account_id == account_id,
        )
    )
    return result.scalar_one_or_none()


async def create_category(
    db: AsyncSession,
    category: schemas.CategoryCreate,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
) -> models.Category:
    db_obj = models.Category(
        name=category.name,
        monthly_limit=category.monthly_limit,
        parent_id=category.parent_id,
        account_id=account_id,
        user_id=user_id,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_category(
    db: AsyncSession,
    category_id: uuid.UUID,
    data: schemas.CategoryUpdate,
    account_id: uuid.UUID,
) -> models.Category | None:
    stmt = (
        update(models.Category)
        .where(
            models.Category.id == category_id, models.Category.account_id == account_id
        )
        .values(**data.model_dump(exclude_unset=True))
        .returning(models.Category)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()


async def delete_category(
    db: AsyncSession, category_id: uuid.UUID, account_id: uuid.UUID
) -> bool:
    count_stmt = (
        select(func.count())
        .select_from(models.Transaction)
        .where(
            models.Transaction.category_id == category_id,
            models.Transaction.account_id == account_id,
        )
    )
    result = await db.execute(count_stmt)
    if result.scalar() > 0:
        return False
    await db.execute(
        delete(models.Category).where(
            models.Category.id == category_id,
            models.Category.account_id == account_id,
        )
    )
    await db.commit()
    return True


# ----------------------------------------------------------------------------
# Операции
# ----------------------------------------------------------------------------


async def get_transactions(
    db: AsyncSession,
    account_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    category_id: uuid.UUID | None = None,
    limit: int | None = None,
):
    stmt = select(models.Transaction).where(models.Transaction.account_id == account_id)
    if start:
        stmt = stmt.where(models.Transaction.created_at >= start)
    if end:
        stmt = stmt.where(models.Transaction.created_at < end)
    if category_id:
        stmt = stmt.where(models.Transaction.category_id == category_id)
    stmt = stmt.order_by(
        models.Transaction.created_at.desc() if limit else models.Transaction.created_at
    )
    if limit:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_transaction(db: AsyncSession, tx_id: uuid.UUID, account_id: uuid.UUID):

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
    account_id: uuid.UUID,
    user_id: uuid.UUID,
) -> models.Transaction:
    rate = await currency.get_rate(tx.currency)
    db_obj = models.Transaction(
        **tx.model_dump(exclude_unset=True),
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
    account_id: uuid.UUID,
    user_id: uuid.UUID,
):
    objects = []
    for tx in txs:
        rate = await currency.get_rate(tx.currency)
        objects.append(
            models.Transaction(
                **tx.model_dump(exclude_unset=True),
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
    tx_id: uuid.UUID,
    data: schemas.TransactionUpdate,
    account_id: uuid.UUID,
) -> models.Transaction | None:
    tx_obj = await get_transaction(db, tx_id, account_id)
    if not tx_obj:
        return None
    update_data = data.model_dump(exclude_unset=True)
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


async def delete_transaction(
    db: AsyncSession, tx_id: uuid.UUID, account_id: uuid.UUID
) -> None:
    await db.execute(
        delete(models.Transaction).where(
            models.Transaction.id == tx_id,
            models.Transaction.account_id == account_id,
        )
    )
    await db.commit()


# ----------------------------------------------------------------------------
# Цели
# ----------------------------------------------------------------------------


async def get_goals(db: AsyncSession, account_id: uuid.UUID):
    result = await db.execute(
        select(models.Goal).where(models.Goal.account_id == account_id)
    )
    return result.scalars().all()


async def get_goal(db: AsyncSession, goal_id: uuid.UUID, account_id: uuid.UUID):
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
    account_id: uuid.UUID,
    user_id: uuid.UUID,
) -> models.Goal:
    db_obj = models.Goal(**goal.model_dump(), account_id=account_id, user_id=user_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_goal(
    db: AsyncSession,
    goal_id: uuid.UUID,
    data: schemas.GoalUpdate,
    account_id: uuid.UUID,
) -> models.Goal | None:
    stmt = (
        update(models.Goal)
        .where(models.Goal.id == goal_id, models.Goal.account_id == account_id)
        .values(**data.model_dump(exclude_unset=True))
        .returning(models.Goal)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()


async def add_to_goal(
    db: AsyncSession,
    goal_id: uuid.UUID,
    amount: float,
    account_id: uuid.UUID,
) -> models.Goal | None:
    """Увеличить накопленную сумму цели."""
    goal = await get_goal(db, goal_id, account_id)
    if not goal:
        return None
    from decimal import Decimal

    goal.current_amount += Decimal(str(amount))
    await db.commit()
    await db.refresh(goal)
    return goal


async def delete_goal(
    db: AsyncSession, goal_id: uuid.UUID, account_id: uuid.UUID
) -> None:
    await db.execute(
        delete(models.Goal).where(
            models.Goal.id == goal_id,
            models.Goal.account_id == account_id,
        )
    )
    await db.commit()


# ----------------------------------------------------------------------------
# Аналитика
# ----------------------------------------------------------------------------


async def transactions_summary_by_category(
    db: AsyncSession, start: datetime, end: datetime, account_id: uuid.UUID
):
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
    db: AsyncSession, start: datetime, end: datetime, account_id: uuid.UUID
):
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
    db: AsyncSession, start: datetime, end: datetime, account_id: uuid.UUID
):
    now = datetime.now(timezone.utc)
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
    db: AsyncSession, start: datetime, end: datetime, account_id: uuid.UUID
):
    day = func.date(models.Transaction.created_at)
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
    db: AsyncSession, start: datetime, end: datetime, account_id: uuid.UUID
):
    now = datetime.now(timezone.utc)
    cutoff = min(now, end)
    stmt = select(func.sum(models.Transaction.amount_rub)).where(
        models.Transaction.created_at >= start,
        models.Transaction.created_at < cutoff,
        models.Transaction.account_id == account_id,
    )
    result = await db.execute(stmt)
    spent = float(result.scalar() or 0)

    if now >= end:
        forecast = spent
    else:
        elapsed_days = (cutoff - start).days + 1
        total_days = (end - start).days
        forecast = spent / elapsed_days * total_days if elapsed_days else 0
    return spent, forecast


# ----------------------------------------------------------------------------
# Регулярные платежи
# ----------------------------------------------------------------------------


async def get_recurring_payments(db: AsyncSession, account_id: uuid.UUID):
    result = await db.execute(
        select(models.RecurringPayment).where(
            models.RecurringPayment.account_id == account_id
        )
    )
    return result.scalars().all()


async def get_recurring_payment(
    db: AsyncSession, rp_id: uuid.UUID, account_id: uuid.UUID
):
    result = await db.execute(
        select(models.RecurringPayment).where(
            models.RecurringPayment.id == rp_id,
            models.RecurringPayment.account_id == account_id,
        )
    )
    return result.scalar_one_or_none()


async def create_recurring_payment(
    db: AsyncSession,
    rp: schemas.RecurringPaymentCreate,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
) -> models.RecurringPayment:
    db_obj = models.RecurringPayment(
        **rp.model_dump(), account_id=account_id, user_id=user_id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_recurring_payment(
    db: AsyncSession,
    rp_id: uuid.UUID,
    data: schemas.RecurringPaymentUpdate,
    account_id: uuid.UUID,
) -> models.RecurringPayment | None:
    stmt = (
        update(models.RecurringPayment)
        .where(
            models.RecurringPayment.id == rp_id,
            models.RecurringPayment.account_id == account_id,
        )
        .values(**data.model_dump(exclude_unset=True))
        .returning(models.RecurringPayment)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()


async def delete_recurring_payment(
    db: AsyncSession, rp_id: uuid.UUID, account_id: uuid.UUID
) -> None:
    await db.execute(
        delete(models.RecurringPayment).where(
            models.RecurringPayment.id == rp_id,
            models.RecurringPayment.account_id == account_id,
        )
    )
    await db.commit()


async def get_recurring_by_day(db: AsyncSession, day: int):
    result = await db.execute(
        select(models.RecurringPayment).where(
            models.RecurringPayment.day == day,
            models.RecurringPayment.active.is_(True),
        )
    )
    return result.scalars().all()


# ----------------------------------------------------------------------------
# Банковские токены
# ----------------------------------------------------------------------------


BANKS = ["tinkoff", "sber", "gazprom"]


async def get_bank_tokens(db: AsyncSession, user_id: uuid.UUID):
    client = vault.get_vault_client()
    items: list[schemas.BankToken] = []
    for bank in BANKS:
        token = await client.read(f"{bank}_token/{user_id}")
        if token is not None:
            items.append(
                schemas.BankToken(
                    id=uuid.uuid4(),
                    bank=bank,
                    token=token,
                    account_id=uuid.uuid4(),
                    user_id=user_id,
                )
            )
    return items


async def get_bank_token(
    db: AsyncSession, bank: str, user_id: uuid.UUID
) -> schemas.BankToken | None:
    """Получить токен конкретного банка."""
    client = vault.get_vault_client()
    token = await client.read(f"{bank}_token/{user_id}")
    if token is None:
        return None
    return schemas.BankToken(
        id=uuid.uuid4(),
        bank=bank,
        token=token,
        account_id=uuid.uuid4(),
        user_id=user_id,
    )


async def set_bank_token(
    db: AsyncSession, bank: str, token: str, user_id: uuid.UUID
) -> schemas.BankToken:
    client = vault.get_vault_client()
    await client.write(f"{bank}_token/{user_id}", token)
    return schemas.BankToken(
        id=uuid.uuid4(),
        bank=bank,
        token=token,
        account_id=uuid.uuid4(),
        user_id=user_id,
    )


async def delete_bank_token(db: AsyncSession, bank: str, user_id: uuid.UUID) -> None:
    client = vault.get_vault_client()
    await client.delete(f"{bank}_token/{user_id}")


# ----------------------------------------------------------------------------
# Push subscriptions
# ----------------------------------------------------------------------------


async def get_push_subscriptions(db: AsyncSession, account_id: uuid.UUID):
    result = await db.execute(
        select(models.PushSubscription).where(
            models.PushSubscription.account_id == account_id
        )
    )
    return result.scalars().all()


async def add_push_subscription(
    db: AsyncSession,
    subscription: schemas.PushSubscriptionCreate,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
) -> models.PushSubscription:
    db_obj = models.PushSubscription(
        **subscription.model_dump(), account_id=account_id, user_id=user_id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_push_subscription(
    db: AsyncSession, sub_id: uuid.UUID, account_id: uuid.UUID
) -> None:
    await db.execute(
        delete(models.PushSubscription).where(
            models.PushSubscription.account_id == account_id,
            models.PushSubscription.id == sub_id,
        )
    )
    await db.commit()
