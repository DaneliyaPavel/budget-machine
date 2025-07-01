from pathlib import Path
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402


def _login(client):
    user = {"email": "goal@example.com", "password": "pass"}
    r = client.post("/пользователи/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/пользователи/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_goal_deposit():
    with TestClient(app) as client:
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post(
            "/цели/",
            json={"name": "Копилка", "target_amount": 1000},
            headers=headers,
        )
        assert r.status_code == 200
        goal_id = r.json()["id"]
        assert r.json()["current_amount"] == 0

        r = client.post(
            f"/цели/{goal_id}/пополнить",
            json={"amount": 150},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["current_amount"] == 150

        r = client.post(
            f"/цели/{goal_id}/пополнить",
            json={"amount": 50},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["current_amount"] == 200
