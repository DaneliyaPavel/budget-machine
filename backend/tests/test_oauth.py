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
from backend.app import oauth  # noqa: E402


def test_tinkoff_oauth_flow(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(oauth, "build_auth_url", lambda: "http://auth")

        async def fake_exchange(code: str) -> str:
            assert code == "code123"
            return "oauth@example.com"

        monkeypatch.setattr(oauth, "exchange_code", fake_exchange)

        r = client.get("/oauth/tinkoff/url")
        assert r.status_code == 200
        assert r.json()["url"] == "http://auth"

        r = client.get("/oauth/tinkoff/callback?code=code123")
        assert r.status_code == 200
        token = r.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        r = client.get("/пользователи/me", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "oauth@example.com"
