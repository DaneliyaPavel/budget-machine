import os
from pathlib import Path
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

DB_PATH = Path("test.db")
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402


def test_tinkoff_mock_login():
    with TestClient(app) as client:
        r = client.get("/auth/tinkoff/mock")
        assert r.status_code == 200
        token = r.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        r = client.get("/users/me", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "mock@tinkoff.dev"
