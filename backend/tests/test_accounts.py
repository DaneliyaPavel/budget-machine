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
async def test_account_read_and_update():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            user = {"email": "acc@example.com", "password": "Password123$"}
            r = await client.post("/users/", json=user)
            assert r.status_code == 200
            token = (
                await client.post(
                    "/users/token",
                    data={"username": user["email"], "password": user["password"]},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            ).json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            r = await client.get("/accounts/me", headers=headers)
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == "Личный бюджет"

            r = await client.patch(
                "/accounts/me",
                json={"id": data["id"], "name": "Семейный", "currency_code": "USD"},
                headers=headers,
            )
            assert r.status_code == 200
            result = r.json()
            assert result["name"] == "Семейный"
            assert result["currency_code"] == "USD"

            r = await client.get(f"/accounts/{data['id']}/balance", headers=headers)
            assert r.status_code == 200
            assert "balance" in r.json()
