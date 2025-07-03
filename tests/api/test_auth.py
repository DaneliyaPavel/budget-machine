import sys
from pathlib import Path
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

# import backend after adjusting path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import backend.app.api.v1.auth as auth_v1
import backend.app.api.v1.users as users_v1
from backend.app.database import engine, Base

app = FastAPI()
app.include_router(auth_v1.router)
app.include_router(users_v1.router)

@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_jwt_cycle():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
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
            r = await client.get("/auth/tinkoff/mock")
            assert r.status_code == 200


@pytest.mark.asyncio
async def test_signup_duplicate():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            data = {"email": "dup@example.com", "password": "Password123$"}
            r = await client.post("/auth/signup", json=data)
            assert r.status_code == 200
            r = await client.post("/auth/signup", json=data)
            assert r.status_code == 400

@pytest.mark.asyncio
async def test_update_user_me():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            data = {"email": "update@example.com", "password": "Password123$"}
            await client.post("/auth/signup", json=data)
            r = await client.post("/auth/login", json=data)
            token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            r = await client.patch("/users/me", json={"email": "changed@example.com"}, headers=headers)
            assert r.status_code == 200
            assert r.json()["email"] == "changed@example.com"
