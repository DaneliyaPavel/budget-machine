import os
import sys
import time
import subprocess
from pathlib import Path
import shutil
import pytest
import redis
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

DB_PATH = Path("test.db")
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402


pytestmark = pytest.mark.skipif(
    shutil.which("redis-server") is None,
    reason="redis-server binary is not available",
)


def _login(client):
    user = {"email": "notif@example.com", "password": "ComplexPass123$"}
    r = client.post("/users/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/users/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_notification_stream():
    proc = subprocess.Popen(
        [
            "redis-server",
            "--port",
            "6379",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    rds = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    # wait for server to be ready
    for _ in range(10):
        try:
            rds.ping()
            break
        except redis.exceptions.ConnectionError:
            time.sleep(0.1)
    rds.flushall()
    try:
        with TestClient(app) as client:
            token = _login(client)
            headers = {"Authorization": f"Bearer {token}"}

            r = client.post(
                "/categories/",
                json={"name": "Нотиф", "monthly_limit": 100},
                headers=headers,
            )
            cat_id = r.json()["id"]

            base_acc = client.get("/accounts/me", headers=headers).json()
            r = client.post("/accounts/", json={"name": "Income"}, headers=headers)
            acc2_id = r.json()["id"]

            tx = {
                "payee": "Магазин",
                "posted_at": "2025-06-15T12:00:00",
                "category_id": cat_id,
                "postings": [
                    {
                        "amount": 150,
                        "side": "debit",
                        "account_id": base_acc["id"],
                        "currency_code": "RUB",
                    },
                    {
                        "amount": 150,
                        "side": "credit",
                        "account_id": acc2_id,
                        "currency_code": "RUB",
                    },
                ],
            }
            client.post("/transactions/", json=tx, headers=headers)

            r = client.get(
                "/аналитика/лимиты?year=2025&month=6&notify=true",
                headers=headers,
            )
            assert r.status_code == 200
            time.sleep(0.5)
            rds = redis.Redis.from_url(
                "redis://localhost:6379/0", decode_responses=True
            )
            messages = rds.xrange("notifications")
            assert len(messages) == 1
            assert "Превышение лимитов" in messages[0][1]["text"]
    finally:
        proc.terminate()
        proc.wait()
