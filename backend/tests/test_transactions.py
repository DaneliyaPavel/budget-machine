import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient
from openpyxl import Workbook
import io

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402


def _login(client, email="tx@example.com"):
    user = {"email": email, "password": "pass"}
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


def test_import_transactions_excel():
    with TestClient(app) as client:
        token = _login(client, email="xlsx@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post("/категории/", json={"name": "Excel"}, headers=headers)
        assert r.status_code == 200
        cat_id = r.json()["id"]

        wb = Workbook()
        ws = wb.active
        ws.append(
            [
                "amount",
                "currency",
                "description",
                "category_id",
                "created_at",
            ]
        )
        ws.append([100, "RUB", "Row1", cat_id, "2025-06-01T12:00:00"])
        ws.append([200, "USD", "Row2", cat_id, "2025-06-02T12:00:00"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        files = {
            "file": (
                "data.xlsx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        r = client.post("/операции/импорт", files=files, headers=headers)
        assert r.status_code == 201
        assert r.json()["created"] == 2

        r = client.get("/операции/", headers=headers)
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 2


def test_transactions_limit():
    with TestClient(app) as client:
        token = _login(client, email="limit2@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post("/категории/", json={"name": "Lim"}, headers=headers)
        cat_id = r.json()["id"]

        for i in range(5):
            tx = {
                "amount": i + 1,
                "currency": "RUB",
                "description": f"#{i}",
                "category_id": cat_id,
            }
            client.post("/операции/", json=tx, headers=headers)

        r = client.get("/операции/?limit=3", headers=headers)
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 3
        assert items[0]["description"] == "#4"
