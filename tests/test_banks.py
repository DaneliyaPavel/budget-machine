import os
from pathlib import Path
import sys
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from app.main import app  # noqa: E402
from app import schemas, vault  # noqa: E402


def _login(client):
    user = {"email": "bank@example.com", "password": "pass"}
    r = client.post("/пользователи/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/пользователи/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


class FakeConnector:
    def __init__(self, user_id, token=None):
        self.token = token
        self.user_id = user_id

    async def fetch_transactions(self, start: datetime, end: datetime):
        return [
            schemas.TransactionCreate(
                amount=100,
                currency="RUB",
                description="test",
                category_id=1,
                created_at=start,
            )
        ]


def test_import_with_saved_token(monkeypatch):
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        # create category
        r = client.post("/категории/", json={"name": "Test"}, headers=headers)
        assert r.status_code == 200

        class FakeVault:
            def __init__(self):
                self.storage = {"tinkoff_token/1": "abc"}

            async def read(self, path):
                return self.storage.get(path)

            async def write(self, path, value):
                self.storage[path] = value

            async def delete(self, path):
                self.storage.pop(path, None)

        fake_vault = FakeVault()
        vault.get_vault_client.cache_clear()
        monkeypatch.setattr(vault, "get_vault_client", lambda: fake_vault)
        monkeypatch.setattr(
            "app.routers.banks.get_connector",
            lambda b, uid, token=None: FakeConnector(uid, token),
        )

        # save bank token
        data = {"bank": "tinkoff", "token": "abc"}
        r = client.post("/токены/", json=data, headers=headers)
        assert r.status_code == 200

        start = "2025-06-01T00:00:00"
        end = "2025-06-30T23:59:59"
        r = client.post(
            f"/банки/импорт_по_токену?bank=tinkoff&start={start}&end={end}",
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["created"] == 1

        r = client.get("/операции/", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
