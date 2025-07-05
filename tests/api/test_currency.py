import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# use sqlite for tests
DB_PATH = Path("test.db")
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402
from backend.app import currency, database  # noqa: E402
from backend.scripts.load_currencies import load_currencies  # noqa: E402
import asyncio  # noqa: E402


async def fake_get_rate(code: str) -> float:
    rates = {"RUB": 1.0, "USD": 90.0, "EUR": 100.0}
    return rates.get(code.upper(), 1.0)


def test_currency_endpoints(monkeypatch):
    monkeypatch.setattr(currency, "get_rate", fake_get_rate)
    currency._rates = {"RUB": 1.0, "USD": 90.0, "EUR": 100.0}

    with TestClient(app) as client:
        r = client.get("/currencies/rates?base=USD")
        assert r.status_code == 200
        data = r.json()
        assert abs(data["EUR"] - (100.0 / 90.0)) < 0.01

        r = client.get("/currencies/convert?amount=100&from=USD&to=EUR")
        assert r.status_code == 200
        assert abs(r.json()["result"] - 90.0) < 0.01


def test_currencies_list(monkeypatch):
    monkeypatch.setattr(currency, "get_rate", fake_get_rate)
    currency._rates = {"RUB": 1.0}

    async def seed():
        async with database.async_session() as session:
            await load_currencies(session)

    asyncio.run(seed())

    with TestClient(app) as client:
        r = client.get("/currencies")
        assert r.status_code == 200
        data = r.json()
        assert any(c["code"] == "USD" for c in data)
