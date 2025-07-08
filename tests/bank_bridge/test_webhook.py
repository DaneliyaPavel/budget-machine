import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from services.bank_bridge.app import app, RAW_TOPIC
from services.bank_bridge import kafka


@pytest.mark.asyncio
async def test_tinkoff_webhook(monkeypatch):
    captured = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        captured.update(
            {
                "topic": topic,
                "user_id": user_id,
                "bank_txn_id": bank_txn_id,
                "data": data,
            }
        )

    monkeypatch.setattr(kafka, "publish", fake_publish)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            payload = {"event": "operation", "payload": {"id": 1, "amount": 10}}
            resp = await cl.post("/webhook/tinkoff/u1", json=payload)
            assert resp.status_code == 200

    assert captured["topic"] == RAW_TOPIC
    assert captured["user_id"] == "u1"
    assert captured["bank_txn_id"] == "1"
    assert captured["data"]["payload"]["amount"] == 10
