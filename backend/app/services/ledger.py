from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas, currency


async def post_entry(
    db: AsyncSession,
    txn: schemas.TransactionCreate,
    postings: list[schemas.PostingCreate],
    account_id: UUID,
    user_id: UUID,
) -> models.Transaction:
    """Insert transaction and postings atomically."""
    async with db.begin():
        rate = await currency.get_rate(txn.currency)
        tx_data = txn.model_dump(exclude_unset=True)
        created = tx_data.get("created_at")
        if created is None:
            created = datetime.now().replace(tzinfo=None)
        elif created.tzinfo is not None:
            created = created.replace(tzinfo=None)
        tx_data["created_at"] = created
        tx_obj = models.Transaction(
            **tx_data,
            amount_rub=txn.amount * rate,
            account_id=account_id,
            user_id=user_id,
        )
        db.add(tx_obj)
        await db.flush()
        for item in postings:
            db.add(
                models.Posting(
                    amount=item.amount,
                    side=item.side,
                    account_id=item.account_id,
                    transaction_id=tx_obj.id,
                )
            )
    await db.refresh(tx_obj)
    return tx_obj


async def get_balance(
    db: AsyncSession,
    account_id: UUID,
    at: datetime | None = None,
) -> float:
    """Return account balance at moment `at`."""
    stmt = (
        select(
            func.coalesce(
                func.sum(
                    case(
                        (models.Posting.side == models.PostingSide.debit, models.Posting.amount),
                        else_=-models.Posting.amount,
                    )
                ),
                0,
            )
        )
        .join(models.Transaction)
        .where(models.Posting.account_id == account_id)
    )
    if at:
        stmt = stmt.where(models.Transaction.created_at <= at)
    result = await db.execute(stmt)
    return float(result.scalar() or 0)


async def stream_transactions(
    db: AsyncSession,
    account_id: UUID,
    start: datetime | None = None,
    end: datetime | None = None,
) -> AsyncGenerator[models.Transaction, None]:
    """Yield transactions one by one ordered by date."""
    stmt = select(models.Transaction).where(models.Transaction.account_id == account_id)
    if start:
        stmt = stmt.where(models.Transaction.created_at >= start)
    if end:
        stmt = stmt.where(models.Transaction.created_at < end)
    stmt = stmt.order_by(models.Transaction.created_at)
    result = await db.stream_scalars(stmt)
    async for row in result:
        yield row
