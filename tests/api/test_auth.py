import os
from pathlib import Path
import sys
import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

db_path = Path("test.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.app.main import app  # noqa: E402


@pytest.mark.asyncio
async def test_jwt_cycle():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            user = {"email": "jwt@example.com", "password": "Password123$"}
            r = await client.post("/auth/signup", json=user)
            assert r.status_code == 200
            r = await client.post("/auth/login", json=user)
            assert r.status_code == 200
            data = r.json()
            token = data["access_token"]
            refresh = data["refresh_token"]
            headers = {"Authorization": f"Bearer {token}"}
            r = await client.get("/users/me", headers=headers)
            assert r.status_code == 200
            r = await client.post("/auth/refresh", json={"refresh_token": refresh})
            assert r.status_code == 200
            new_token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {new_token}"}
            r = await client.get("/users/me", headers=headers)
            assert r.status_code == 200
