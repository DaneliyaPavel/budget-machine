import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app import database
from alembic.config import Config
from alembic import command


@pytest_asyncio.fixture
async def migrated_pg():
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
        cfg = Config("alembic.ini")
        cfg.set_main_option(
            "sqlalchemy.url",
            os.environ["DATABASE_URL"].replace("+asyncpg", "+psycopg"),
        )
        command.upgrade(cfg, "head")
    except Exception:
        await engine.dispose()
        database.engine = old_engine
        database.async_session = old_sessionmaker
        if old_url is not None:
            os.environ["DATABASE_URL"] = old_url
        pytest.skip("PostgreSQL server is not available")

    database.engine = engine
    database.async_session = sessionmaker
    yield engine
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()
    database.engine = old_engine
    database.async_session = old_sessionmaker
    if old_url is not None:
        os.environ["DATABASE_URL"] = old_url


@pytest.mark.asyncio
async def test_indexes_created(migrated_pg):
    async with migrated_pg.connect() as conn:
        result = await conn.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename='accounts'")
        )
        names = {row[0] for row in result}
        assert "accounts_user_id_idx" in names

        result = await conn.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename='categories'")
        )
        names = {row[0] for row in result}
        assert "categories_user_id_idx" in names

        result = await conn.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename='transactions'")
        )
        names = {row[0] for row in result}
        assert "transactions_user_posted_idx" in names

        result = await conn.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename='postings'")
        )
        names = {row[0] for row in result}
        assert "postings_txn_id_idx" in names
