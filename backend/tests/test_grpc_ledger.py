import os
import sys
from pathlib import Path
import uuid

import pytest
from sqlalchemy import text
import pytest_asyncio
from grpclib.testing import ChannelFor

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app import database, models  # noqa: E402
from backend.app.grpc.server import LedgerService  # noqa: E402
from backend.app.grpc import ledger_grpc, ledger_pb2  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
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


async def _prepare_entities(session):
    acc1 = models.Account(name="Cash", currency_code="RUB")
    acc2 = models.Account(name="Income", currency_code="RUB")
    user = models.User(email="u@example.com", hashed_password="x", account=acc1)
    cat = models.Category(name="Misc", account=acc1, user=user)
    session.add_all([acc1, acc2, user, cat])
    await session.commit()
    return acc1, acc2, user, cat


@pytest.mark.asyncio
async def test_grpc_post_entry_and_stream():
    service = LedgerService()
    async with ChannelFor([service]) as channel:
        stub = ledger_grpc.LedgerServiceStub(channel)
        async with database.async_session() as session:
            acc1, acc2, user, cat = await _prepare_entities(session)

        req = ledger_pb2.PostEntryRequest(
            amount=100,
            currency="RUB",
            description="test",
            category_id=str(cat.id),
            postings=[
                ledger_pb2.Posting(amount=100, side="debit", account_id=str(acc1.id)),
                ledger_pb2.Posting(amount=100, side="credit", account_id=str(acc2.id)),
            ],
            account_id=str(acc1.id),
            user_id=str(user.id),
        )
        tx_id = await stub.PostEntry(req)
        assert tx_id.id

        bal1 = await stub.GetBalance(
            ledger_pb2.BalanceRequest(account_id=str(acc1.id))
        )
        bal2 = await stub.GetBalance(
            ledger_pb2.BalanceRequest(account_id=str(acc2.id))
        )
        assert bal1.amount == 100
        assert bal2.amount == -100

        txns = []
        async for item in stub.StreamTxns(
            ledger_pb2.StreamRequest(account_id=str(acc1.id))
        ):
            txns.append(item)
        assert len(txns) == 1
