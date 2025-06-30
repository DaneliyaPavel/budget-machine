import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from app.main import app


def _login(client):
    user = {"email": "tx@example.com", "password": "pass"}
    r = client.post("/пользователи/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/пользователи/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_export_transactions():
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        # create category
        r = client.post("/категории/", json={"name": "Продукты"}, headers=headers)
        assert r.status_code == 200
        cat_id = r.json()["id"]

        tx1 = {
            "amount": 100,
            "currency": "RUB",
            "description": "Магазин",
            "category_id": cat_id,
        }
        tx2 = {
            "amount": 50,
            "currency": "USD",
            "description": "Amazon",
            "category_id": cat_id,
        }
        client.post("/операции/", json=tx1, headers=headers)
        client.post("/операции/", json=tx2, headers=headers)

        r = client.get("/операции/экспорт", headers=headers)
        assert r.status_code == 200
        lines = r.text.strip().splitlines()
        assert len(lines) == 3
        assert lines[0].startswith("id,amount,currency")
