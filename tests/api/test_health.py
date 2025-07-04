import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from backend.app.main import app


@pytest.mark.asyncio
async def test_health():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
