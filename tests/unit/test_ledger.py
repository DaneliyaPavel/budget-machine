import os
import sys
from pathlib import Path
import uuid
import pytest
from sqlalchemy import select, func, text
import pytest_asyncio

# add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app import database, models, schemas
from backend.app.services import ledger


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # store previous engine and session maker
    old_engine = database.engine
    old_sessionmaker = database.async_session
    old_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = (
        "postgresql+asyncpg://testuser:testpass@localhost/testuserdb"
    )

    await old_engine.dispose()
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.run_sync(database.Base.metadata.create_all)
            uid = uuid.uuid4()
            await conn.execute(
                text(
                    "INSERT INTO currencies(id, code, name, symbol, precision) "
                    "VALUES(:id, 'RUB', 'Ruble', '₽', 2)"
                ),
                {"id": uid},
            )
            await conn.execute(
                text(
                    """
                    CREATE OR REPLACE FUNCTION check_postings_balance()
                    RETURNS TRIGGER AS $$
                    DECLARE
                        txid uuid;
                        deb NUMERIC;
                        cred NUMERIC;
                    BEGIN
                        IF TG_OP = 'DELETE' THEN
                            txid := OLD.transaction_id;
                        ELSE
                            txid := NEW.transaction_id;
                        END IF;
                        SELECT COALESCE(SUM(amount) FILTER (WHERE side='debit'), 0),
                               COALESCE(SUM(amount) FILTER (WHERE side='credit'), 0)
                        INTO deb, cred
                        FROM postings WHERE transaction_id = txid;
                        IF deb <> cred THEN
                            RAISE EXCEPTION 'Debit and credit totals do not match for transaction %', txid;
                        END IF;
                        IF TG_OP = 'DELETE' THEN
                            RETURN OLD;
                        ELSE
                            RETURN NEW;
                        END IF;
                    END;
                    $$ LANGUAGE plpgsql;
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    CREATE CONSTRAINT TRIGGER postings_balance_check
                    AFTER INSERT OR UPDATE OR DELETE ON postings
                    DEFERRABLE INITIALLY DEFERRED
                    FOR EACH ROW EXECUTE FUNCTION check_postings_balance()
                    """
                )
            )
    except Exception:
        await engine.dispose()
        database.engine = old_engine
        database.async_session = old_sessionmaker
        if old_url is not None:
            os.environ["DATABASE_URL"] = old_url
        pytest.skip("PostgreSQL server is not available")

    database.engine = engine
    database.async_session = sessionmaker
    yield
    async with database.engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await database.engine.dispose()
    database.engine = old_engine
    database.async_session = old_sessionmaker
    if old_url is not None:
        os.environ["DATABASE_URL"] = old_url


async def _prepare_entities(session: AsyncSession):
    acc1 = models.Account(name="Cash", currency_code="RUB")
    acc2 = models.Account(name="Income", currency_code="RUB")
    user = models.User(email="u@example.com", hashed_password="x", account=acc1)
    cat = models.Category(name="Misc", account=acc1, user=user)
    session.add_all([acc1, acc2, user, cat])
    await session.commit()
    return acc1, acc2, user, cat


@pytest.mark.asyncio
async def test_post_entry_and_stream():
    async with database.async_session() as session:
        acc1, acc2, user, cat = await _prepare_entities(session)
        tx = schemas.TransactionCreate(category_id=cat.id)
        postings = [
            schemas.PostingCreate(amount=100, side="debit", account_id=acc1.id),
            schemas.PostingCreate(amount=100, side="credit", account_id=acc2.id),
        ]
        await ledger.post_entry(session, tx, postings, acc1.id, user.id)

        bal1 = await ledger.get_balance(session, acc1.id)
        bal2 = await ledger.get_balance(session, acc2.id)
        assert bal1 == 100
        assert bal2 == -100

        rows = []
        async for item in ledger.stream_transactions(session, acc1.id):
            rows.append(item)
        assert len(rows) == 1


@pytest.mark.asyncio
async def test_post_entry_atomicity():
    async with database.async_session() as session:
        acc1, acc2, user, cat = await _prepare_entities(session)
        tx = schemas.TransactionCreate(category_id=cat.id)
        postings = [
            schemas.PostingCreate(amount=100, side="debit", account_id=acc1.id),
            schemas.PostingCreate(amount=50, side="credit", account_id=acc2.id),
        ]
        with pytest.raises(Exception):
            await ledger.post_entry(session, tx, postings, acc1.id, user.id)

        count_tx = await session.scalar(
            select(func.count()).select_from(models.Transaction)
        )
        count_post = await session.scalar(
            select(func.count()).select_from(models.Posting)
        )
        assert count_tx == 0
        assert count_post == 0
