import os
import sys
from pathlib import Path
import pytest_asyncio

# add repository root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ensure DATABASE_URL is set before backend modules import
DB_PATH = Path("test.db")
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.database import engine, async_session, Base  # noqa: E402


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()


@pytest_asyncio.fixture
async def session():
    async with async_session() as s:
        yield s
