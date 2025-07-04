from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

import contextlib
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from .. import models, schemas


async def post_entry(
    db: AsyncSession,
    txn: schemas.TransactionCreate,
    postings: list[schemas.PostingCreate],
    account_id: UUID,
    user_id: UUID,
) -> models.Transaction:
    """Insert transaction and postings atomically."""
    if len(postings) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two postings required",
        )
    started = not db.in_transaction()
    ctx = db.begin() if started else contextlib.nullcontext()
    async with ctx:
        tx_data = {
            k: v
            for k, v in txn.model_dump(exclude_unset=True).items()
            if k in {"posted_at", "payee", "note", "external_id"}
        }
        posted = tx_data.get("posted_at")
        if posted is None:
            posted = datetime.now().replace(tzinfo=None)
        elif posted.tzinfo is not None:
            posted = posted.replace(tzinfo=None)
        tx_data["posted_at"] = posted
        tx_obj = models.Transaction(**tx_data, user_id=user_id)
        db.add(tx_obj)
        await db.flush()
        for item in postings:
            db.add(
                models.Posting(
                    amount=item.amount,
                    side=item.side,
                    currency_code=item.currency_code,
                    account_id=item.account_id,
                    transaction_id=tx_obj.id,
                )
            )
    if started:
        await db.refresh(tx_obj)
    else:
        await db.commit()
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
                        (
                            models.Posting.side == models.PostingSide.debit,
                            models.Posting.amount,
                        ),
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
        stmt = stmt.where(models.Transaction.posted_at <= at)
    result = await db.execute(stmt)
    return float(result.scalar() or 0)


async def stream_transactions(
    db: AsyncSession,
    account_id: UUID,
    start: datetime | None = None,
    end: datetime | None = None,
) -> AsyncGenerator[models.Transaction, None]:
    """Yield transactions one by one ordered by date."""
    stmt = (
        select(models.Transaction)
        .join(models.Posting)
        .where(models.Posting.account_id == account_id)
    )
    if start:
        stmt = stmt.where(models.Transaction.posted_at >= start)
    if end:
        stmt = stmt.where(models.Transaction.posted_at < end)
    stmt = stmt.order_by(models.Transaction.posted_at)
    result = await db.stream_scalars(stmt)
    async for row in result:
        yield row
