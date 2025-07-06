import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402
from backend.app import vault  # noqa: E402


def _login(client):
    user = {"email": "tok@example.com", "password": "ComplexPass123$"}
    r = client.post("/users/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/users/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


class FakeVault:
    def __init__(self):
        self.storage = {}

    async def read(self, path):
        return self.storage.get(path)

    async def write(self, path, value):
        self.storage[path] = value

    async def delete(self, path):
        self.storage.pop(path, None)


def test_token_crud(monkeypatch):
    fake = FakeVault()
    vault.get_vault_client.cache_clear()
    monkeypatch.setattr(vault, "get_vault_client", lambda: fake)
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        data = {"bank": "tinkoff", "token": "abc"}
        r = client.post("/токены/", json=data, headers=headers)
        assert r.status_code == 200

        r = client.get("/токены/", headers=headers)
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["bank"] == "tinkoff"

        r = client.delete(f"/токены/{data['bank']}", headers=headers)
        assert r.status_code == 204

        r = client.get("/токены/", headers=headers)
        assert r.status_code == 200
        assert r.json() == []
