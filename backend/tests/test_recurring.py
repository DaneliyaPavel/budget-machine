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


def _login(client, email="test@example.com", password="pass"):
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


def test_recurring_crud():
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        # create category for payment
        r = client.post("/categories/", json={"name": "Подписки"}, headers=headers)
        assert r.status_code == 200
        cat_id = r.json()["id"]

        item = {
            "name": "Netflix",
            "amount": 10,
            "currency": "USD",
            "day": 5,
            "category_id": cat_id,
        }
        r = client.post("/регулярные/", json=item, headers=headers)
        assert r.status_code == 200
        rp_id = r.json()["id"]

        r = client.get("/регулярные/", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

        r = client.patch(
            f"/регулярные/{rp_id}",
            json={"amount": 12},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["amount"] == 12

        r = client.delete(f"/регулярные/{rp_id}", headers=headers)
        assert r.status_code == 204
        r = client.get("/регулярные/", headers=headers)
        assert r.status_code == 200
        assert r.json() == []


def test_recurring_task_creates_transactions():
    with TestClient(app) as client:
        token = _login(client, email="task@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        # category
        r = client.post("/categories/", json={"name": "Подписки"}, headers=headers)
        cat_id = r.json()["id"]

        # create recurring payment for day 5
        item = {
            "name": "Spotify",
            "amount": 10,
            "currency": "USD",
            "day": 5,
            "category_id": cat_id,
        }
        r = client.post("/регулярные/", json=item, headers=headers)
        assert r.status_code == 200

        # run task for 2025-06-05
        from backend.app import tasks

        created = tasks.process_recurring_task("2025-06-05T00:00:00")
        assert created == 1

        r = client.get("/transactions/", headers=headers)
        assert r.status_code == 200
        # recurring transactions do not create postings
        assert r.json() == []
