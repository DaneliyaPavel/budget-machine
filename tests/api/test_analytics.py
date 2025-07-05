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


def _login(client, email="ana@example.com", password="pass"):
    user = {"email": email, "password": password}
    r = client.post("/users/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/users/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_analytics_endpoints():
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        acc = client.get("/accounts/me", headers=headers).json()
        r = client.post("/accounts/", json={"name": "Income"}, headers=headers)
        assert r.status_code == 200
        acc2 = r.json()["id"]

        # create category
        r = client.post(
            "/categories/", json={"name": "Еда", "monthly_limit": 200}, headers=headers
        )
        assert r.status_code == 200
        cat_id = r.json()["id"]

        # create transactions for June 2025
        tx1 = {
            "payee": "Магазин",
            "posted_at": "2025-06-05T12:00:00",
            "category_id": cat_id,
            "postings": [
                {
                    "amount": 100,
                    "side": "debit",
                    "account_id": acc["id"],
                    "currency_code": "RUB",
                },
                {
                    "amount": 100,
                    "side": "credit",
                    "account_id": acc2,
                    "currency_code": "RUB",
                },
            ],
        }
        tx2 = {
            "payee": "Кафе",
            "posted_at": "2025-06-15T12:00:00",
            "category_id": cat_id,
            "postings": [
                {
                    "amount": 50,
                    "side": "debit",
                    "account_id": acc["id"],
                    "currency_code": "RUB",
                },
                {
                    "amount": 50,
                    "side": "credit",
                    "account_id": acc2,
                    "currency_code": "RUB",
                },
            ],
        }
        client.post("/transactions/", json=tx1, headers=headers)
        client.post("/transactions/", json=tx2, headers=headers)

        # create goal and deposit
        r = client.post(
            "/цели/", json={"name": "Отпуск", "target_amount": 500}, headers=headers
        )
        goal_id = r.json()["id"]
        client.post(f"/цели/{goal_id}/пополнить", json={"amount": 150}, headers=headers)

        # summary by category
        r = client.get("/аналитика/категории?year=2025&month=6", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data == [{"category": "Еда", "total": 150.0}]

        # summary by day
        r = client.get("/аналитика/дни?year=2025&month=6", headers=headers)
        assert r.status_code == 200
        days = {d["date"][:10]: d["total"] for d in r.json()}
        assert days["2025-06-05"] == 100.0
        assert days["2025-06-15"] == 50.0

        # balance overview
        r = client.get("/аналитика/баланс?year=2025&month=6", headers=headers)
        assert r.status_code == 200
        bal = r.json()
        assert bal["spent"] == 150.0
        assert bal["forecast"] >= 150.0

        # goals progress
        r = client.get("/аналитика/цели", headers=headers)
        assert r.status_code == 200
        g = r.json()[0]
        assert g["name"] == "Отпуск"
        assert g["current_amount"] == 150.0
        assert abs(g["progress"] - 30.0) < 0.01
