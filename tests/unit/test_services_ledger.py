import pytest
from datetime import timezone
from fastapi import HTTPException

from backend.app import schemas, crud
from backend.app.database import async_session
from backend.app.services import ledger


@pytest.mark.asyncio
async def test_post_entry_and_balance(session):
    user = await crud.create_user(
        session, schemas.UserCreate(email="a@b.c", password="ComplexPass123$")
    )
    category = await crud.create_category(
        session, schemas.CategoryCreate(name="Food"), user.account_id, user.id
    )

    # create second account for postings
    account2 = await crud.create_account(
        session,
        schemas.AccountCreate(name="Income", currency_code="RUB", user_id=user.id),
    )

    txn = schemas.TransactionCreate(category_id=category.id)
    postings = [
        schemas.PostingCreate(
            amount=100, side="debit", account_id=user.account_id, currency_code="RUB"
        ),
        schemas.PostingCreate(
            amount=100, side="credit", account_id=account2.id, currency_code="RUB"
        ),
    ]
    async with async_session() as db:
        tx = await ledger.post_entry(db, txn, postings, user.account_id, user.id)
        assert tx.posted_at.tzinfo == timezone.utc

        balance = await ledger.get_balance(db, user.account_id)
        assert balance == 100

        txns = [t async for t in ledger.stream_transactions(db, user.account_id)]
    assert len(txns) == 1
    assert txns[0].id == tx.id


@pytest.mark.asyncio
async def test_post_entry_requires_two_postings(session):
    user = await crud.create_user(
        session, schemas.UserCreate(email="b@b.c", password="ComplexPass123$")
    )
    category = await crud.create_category(
        session, schemas.CategoryCreate(name="Misc"), user.account_id, user.id
    )
    txn = schemas.TransactionCreate(category_id=category.id)
    postings = [
        schemas.PostingCreate(
            amount=50, side="debit", account_id=user.account_id, currency_code="RUB"
        )
    ]
    async with async_session() as db:
        with pytest.raises(HTTPException):
            await ledger.post_entry(db, txn, postings, user.account_id, user.id)


@pytest.mark.asyncio
async def test_post_entry_mismatched_totals(session):
    """DB should raise error if debit and credit totals differ."""
    from sqlalchemy import text

    async with async_session() as setup_db:
        await setup_db.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS postings_balance_check
                AFTER INSERT ON postings
                BEGIN
                    SELECT CASE WHEN (
                        SELECT COALESCE(SUM(CASE WHEN side='debit' THEN amount ELSE -amount END), 0)
                        FROM postings
                        WHERE transaction_id = NEW.transaction_id
                    ) != 0 THEN RAISE(ABORT, 'mismatch') END;
                END;
                """
            )
        )

    user = await crud.create_user(
        session, schemas.UserCreate(email="c@b.c", password="ComplexPass123$")
    )
    category = await crud.create_category(
        session, schemas.CategoryCreate(name="Err"), user.account_id, user.id
    )
    account2 = await crud.create_account(
        session,
        schemas.AccountCreate(name="Income", currency_code="RUB", user_id=user.id),
    )

    txn = schemas.TransactionCreate(category_id=category.id)
    postings = [
        schemas.PostingCreate(
            amount=100, side="debit", account_id=user.account_id, currency_code="RUB"
        ),
        schemas.PostingCreate(
            amount=50, side="credit", account_id=account2.id, currency_code="RUB"
        ),
    ]
    async with async_session() as db:
        with pytest.raises(Exception):
            await ledger.post_entry(db, txn, postings, user.account_id, user.id)
