from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import UUID

import contextlib
from sqlalchemy import select, func, case
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from ..api.utils import api_error

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
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "At least two postings required",
            "INVALID_POSTINGS",
        )
    started = not db.in_transaction()
    ctx = db.begin() if started else contextlib.nullcontext()
    async with ctx:
        tx_data = {
            k: v
            for k, v in txn.model_dump(exclude_unset=True).items()
            if k in {"posted_at", "payee", "note", "external_id", "category_id"}
        }
        posted = tx_data.get("posted_at")
        if posted is None:
            posted = datetime.now(timezone.utc)
        elif posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        else:
            posted = posted.astimezone(timezone.utc)
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
    await db.commit()
    await db.refresh(tx_obj)
    if tx_obj.posted_at.tzinfo is None:
        tx_obj.posted_at = tx_obj.posted_at.replace(tzinfo=timezone.utc)
    else:
        tx_obj.posted_at = tx_obj.posted_at.astimezone(timezone.utc)
    return tx_obj


async def get_balance(
    db: AsyncSession,
    account_id: UUID,
    at: datetime | None = None,
) -> Decimal:
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
    value = result.scalar()
    return Decimal(value) if value is not None else Decimal("0")


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
        if row.posted_at.tzinfo is None:
            row.posted_at = row.posted_at.replace(tzinfo=timezone.utc)
        else:
            row.posted_at = row.posted_at.astimezone(timezone.utc)
        yield row
