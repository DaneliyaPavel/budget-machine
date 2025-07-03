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
from backend.app import tasks  # noqa: E402


def _login(client, email="job@example.com"):
    user = {"email": email, "password": "pass"}
    r = client.post("/users/", json=user)
    assert r.status_code == 200
    r = client.post(
        "/users/token",
        data={"username": user["email"], "password": user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


class DummyRes:
    def __init__(self, id="123"):
        self.id = id


def test_import_job(monkeypatch):
    with TestClient(app) as client:
        token = _login(client, email="import@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        # category
        r = client.post("/categories/", json={"name": "Job"}, headers=headers)
        assert r.status_code == 200

        called = {}

        def fake_delay(*args, **kwargs):
            called["args"] = args
            return DummyRes()

        monkeypatch.setattr(tasks.import_transactions_task, "delay", fake_delay)

        start = "2025-06-01T00:00:00"
        end = "2025-06-30T23:59:59"
        r = client.post(
            f"/задания/импорт?bank=tinkoff&token=abc&start={start}&end={end}",
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["task_id"] == "123"
        assert called["args"][0] == "tinkoff"


def test_limits_job(monkeypatch):
    with TestClient(app) as client:
        token = _login(client, email="limit@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        def fake_delay(account_id, year, month):
            assert year == 2025
            assert month == 6
            return DummyRes("456")

        monkeypatch.setattr(tasks.check_limits_task, "delay", fake_delay)

        r = client.post(
            "/задания/лимиты?year=2025&month=6",
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["task_id"] == "456"


def test_get_job_status(monkeypatch):
    with TestClient(app) as client:
        res = DummyRes()
        res.status = "SUCCESS"
        res.result = 5
        res.ready = lambda: True
        monkeypatch.setattr(tasks.celery_app, "AsyncResult", lambda tid: res)
        r = client.get("/задания/123")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "SUCCESS"
        assert data["result"] == 5
