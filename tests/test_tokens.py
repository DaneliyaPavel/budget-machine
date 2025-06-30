import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from app.main import app  # noqa: E402


def _login(client):
    user = {"email": "tok@example.com", "password": "pass"}
    r = client.post("/пользователи/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/пользователи/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_token_crud():
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
