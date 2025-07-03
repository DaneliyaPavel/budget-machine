import pytest
from fastapi import HTTPException

from backend.app import schemas, crud, currency
from backend.app.database import async_session
from backend.app.services import ledger


@pytest.mark.asyncio
async def test_post_entry_and_balance(session, monkeypatch):
    user = await crud.create_user(
        session, schemas.UserCreate(email="a@b.c", password="Pwd123$")
    )
    category = await crud.create_category(
        session, schemas.CategoryCreate(name="Food"), user.account_id, user.id
    )

    async def fake_rate(code: str) -> float:
        return 1.0

    monkeypatch.setattr(currency, "get_rate", fake_rate)

    # create second account for postings
    account2 = await crud.create_account(
        session,
        schemas.AccountCreate(name="Income", currency_code="RUB", user_id=user.id),
    )

    txn = schemas.TransactionCreate(amount=100, currency="RUB", category_id=category.id)
    postings = [
        schemas.PostingCreate(amount=100, side="debit", account_id=user.account_id),
        schemas.PostingCreate(amount=100, side="credit", account_id=account2.id),
    ]
    async with async_session() as db:
        tx = await ledger.post_entry(db, txn, postings, user.account_id, user.id)
        assert tx.amount == 100

        balance = await ledger.get_balance(db, user.account_id)
        assert balance == 100

        txns = [t async for t in ledger.stream_transactions(db, user.account_id)]
    assert len(txns) == 1
    assert txns[0].id == tx.id


@pytest.mark.asyncio
async def test_post_entry_requires_two_postings(session):
    user = await crud.create_user(
        session, schemas.UserCreate(email="b@b.c", password="Pwd123$")
    )
    category = await crud.create_category(
        session, schemas.CategoryCreate(name="Misc"), user.account_id, user.id
    )
    txn = schemas.TransactionCreate(amount=50, currency="RUB", category_id=category.id)
    postings = [
        schemas.PostingCreate(amount=50, side="debit", account_id=user.account_id)
    ]
    async with async_session() as db:
        with pytest.raises(HTTPException):
            await ledger.post_entry(db, txn, postings, user.account_id, user.id)
